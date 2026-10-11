"""QuestLog event40の実同期dispatchによる最小Thumb code-role証明。

これは保存状態の実行・全QuestLog入力安全性・GetMapNameの復帰性の証明ではない。
BLのreturn successorを含む静的命令型だけを固定し、donor leaseには用いない。
"""
import hashlib
import re

import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_code as code
from pr16_dex_hof_script_engine import ThumbConsumer
from pr16_dex_hof_reference_gaps import CANDIDATE

need, identity, chunk = d.need, d.identity, d.chunk
HIT = 0x081161EB
ENTRY = 0x081161D8
DISPATCH = 0x0811460C
EVENT_ID = 40
TABLE = 0x08416E8C
SIZE_TABLE = 0x08416F38
KIND = 'rooted_thumb_instruction_stream'
COMMIT = 'c75f352304d529f6ba92d4f74b9cf8b5c3810788'
WINDOWS = {
    'dispatcher_null_and_action_guard': (DISPATCH, 22),
    'dispatcher_guard_global': (0x08114624, 4),
    'dispatcher_selector_and_indirect_call': (0x08114628, 20),
    'dispatcher_failure_return': (0x08114656, 6),
    'dispatcher_table_and_event_mask': (0x0811465C, 8),
    'event40_function_slot': (TABLE + 4 * EVENT_ID, 4),
    'indirect_bx_r1': (0x081C7ACC, 2),
    'event_payload_reader': (0x081149AC, 26),
    'event_payload_reader_literals': (0x081149C8, 8),
    'event40_size_slot': (SIZE_TABLE + EVENT_ID, 1),
    'handler_entry_to_hit': (ENTRY, 18),
    'hit_instruction_window': (0x081161EA, 6),
    'handler_text_destinations': (0x08116210, 8),
}
CLAIMS = {
    'proof_scope': 'static_actual_dispatch_and_complete_instruction_roles',
    'full_story_reachability_claimed': False,
    'runtime_execution_observed': False,
    'all_entry_states_safe_claimed': False,
    'get_map_name_return_proven': False,
    'BL_return_successor_is_static_code_role_only': True,
    'literal_pool_included': False,
    'whole_function_range_classified': False,
    'indirect_reference_completeness_claimed': False,
    'donor_eligible': False,
    'donor_leased': False,
}
# Fixed public-source identities are independent of the caller's review metadata.
SOURCE_IDS = {'pret-quest_log_events.c': {'local': 'pret-quest_log_events.c', 'repository': 'pret/pokefirered', 'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788', 'path': 'src/quest_log_events.c', 'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/quest_log_events.c', 'size': 88060, 'sha256': 'e6cade44e4c41d0c2a0b27a718ffaee16a9485d36e7f09d6adc9da752b7b7e36', 'git_blob_sha': '7714d887a13be5ab9ca3b4e75edfc5f412e993f8'}, 'pret-quest_log.h': {'local': 'pret-quest_log.h', 'repository': 'pret/pokefirered', 'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788', 'path': 'include/quest_log.h', 'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/include/quest_log.h', 'size': 6648, 'sha256': '0bfe5b360ea2a888534d25c00a0084781821b975fd01475b0d1074021c89ffb5', 'git_blob_sha': '279786985a6b79d76b78dcd745056087645e7d1b'}, 'pret-quest_log_constants.h': {'local': 'pret-quest_log_constants.h', 'repository': 'pret/pokefirered', 'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788', 'path': 'include/constants/quest_log.h', 'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/include/constants/quest_log.h', 'size': 6408, 'sha256': '90cceec5883201c3d3d2bdb420d1f7b3ebef21f4716eef0760bba507559be2dc', 'git_blob_sha': 'fe284ba133ccc28053515c501979741b3960212f'}}


def half(raw, a):
    return int.from_bytes(chunk(raw, a, 2), 'little')


def sources_bind(review, sources):
    need(set(sources) == set(SOURCE_IDS), 'exact three QuestLog source roles')
    need(review['source_bindings'] == SOURCE_IDS, 'independent fixed source provenance')
    for name, expected in SOURCE_IDS.items():
        raw = sources[name]
        need(identity(raw) == {k: expected[k] for k in ('size', 'sha256')}, 'whole source identity')
        need(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == expected['git_blob_sha'], 'whole public Git blob')
    src = sources['pret-quest_log_events.c'].decode()
    hdr = sources['pret-quest_log.h'].decode()
    const = sources['pret-quest_log_constants.h'].decode()
    need(re.search(r'#define\s+QL_EVENT_OBTAINED_STORY_ITEM\s+40\b', const), 'public event40 selector')
    need(re.search(r'#define\s+QL_CMD_EVENT_MASK\s+0x0FFF\b', hdr), 'public 12-bit event mask')
    need('[QL_EVENT_OBTAINED_STORY_ITEM]           = LoadEvent_ObtainedStoryItem' in src, 'public handler table role')
    need('sLoadEventFuncs[(r0[0] & QL_CMD_EVENT_MASK)](eventData)' in src, 'public synchronous event dispatcher')
    need('GetMapNameGeneric(gStringVar1, r5[0]);' in src, 'public typed handler call role')


def semantic_consumers(raw):
    """Every selected instruction has an independent operand/control-flow check."""
    s = ThumbConsumer(raw)
    def hmem(a, load, rd, rb, offset):
        need(offset % 2 == 0, 'halfword field alignment')
        s.opcode(a, 0x8000 | (0x800 if load else 0) | ((offset // 2) << 6) | (rb << 3) | rd, 'LDRH/STRH field')
    def alu(a, mode, rd, rs):
        s.opcode(a, 0x4000 | (mode << 6) | (rs << 3) | rd, 'selected ALU register flow')
    # QL_LoadEvent: null guard, unsigned action-time guard, table selector and ABI.
    s.stack(DISPATCH, False, 1 << 4, True)
    s.addi(0x0811460E, 4, 0, 0)
    s.imm(0x08114610, 'cmp', 0, 0)
    s.branch(0x08114612, 0, 0x0811461E)
    s.pointer(0x08114614, 1, 0x08114624)
    hmem(0x08114616, True, 0, 0, 2)
    hmem(0x08114618, True, 1, 1, 0)
    s.compare(0x0811461A, 0, 1)
    s.branch(0x0811461C, 9, 0x08114628)
    s.imm(0x0811461E, 'mov', 0, 0)
    s.jump(0x08114620, 0x08114656)
    s.stack(0x08114656, True, 1 << 4)
    s.stack(0x08114658, True, 1 << 1)
    s.bx(0x0811465A, 1)
    s.pointer(0x08114628, 2, 0x0811465C)
    hmem(0x0811462A, True, 1, 4, 0)
    s.pointer(0x0811462C, 0, 0x08114660)
    alu(0x0811462E, 0, 0, 1)
    s.shift(0x08114630, False, 0, 0, 2)
    s.add(0x08114632, 0, 0, 2)
    s.mem(0x08114634, True, False, 1, 0, 0)
    s.addi(0x08114636, 0, 4, 0)
    s.call(0x08114638, 0x081C7ACC)
    s.bx(0x081C7ACC, 1)
    # LoadEvent(40,event): pure reader, no call or store. Payload=event+4+4*counter.
    s.shift(0x081149AC, False, 0, 0, 16)
    s.shift(0x081149AE, True, 0, 0, 16)
    s.pointer(0x081149B0, 2, 0x081149C8)
    hmem(0x081149B2, True, 3, 2, 2)
    s.pointer(0x081149B4, 2, 0x081149CC)
    s.add(0x081149B6, 0, 0, 2)
    s.mem(0x081149B8, True, True, 0, 0, 0)
    s.opcode(0x081149BA, 0x3800 | 4, 'SUB r0 immediate4 header size')
    alu(0x081149BC, 13, 0, 3)
    s.imm(0x081149BE, 'add', 0, 4)
    s.add(0x081149C0, 1, 1, 0)
    s.addi(0x081149C2, 0, 1, 0)
    s.bx(0x081149C4, 14)
    # Registered handler entry reaches complete BL; next LDR is its return successor.
    s.stack(ENTRY, False, (1 << 4) | (1 << 5) | (1 << 6), True)
    s.addi(0x081161DA, 1, 0, 0)
    s.imm(0x081161DC, 'mov', 0, EVENT_ID)
    s.call(0x081161DE, 0x081149AC)
    s.addi(0x081161E2, 4, 0, 0)
    s.addi(0x081161E4, 5, 4, 2)
    s.pointer(0x081161E6, 0, 0x08116210)
    s.mem(0x081161E8, True, True, 1, 4, 2)
    s.call(0x081161EA, 0x080C5FDC)
    s.pointer(0x081161EE, 6, 0x08116214)
    expected = {
        0x08114624: 0x0203AF10, 0x0811465C: TABLE, 0x08114660: 0xFFF,
        TABLE + 4 * EVENT_ID: ENTRY | 1,
        0x081149C8: 0x0203AFBC, 0x081149CC: SIZE_TABLE,
        0x08116210: 0x02021C4C, 0x08116214: 0x02021C60,
    }
    need(all(d.u32(raw, a) == v for a, v in expected.items()), 'actual immutable selector, mask, globals and destinations')
    need(chunk(raw, SIZE_TABLE + EVENT_ID, 1) == bytes([8]), 'event40 four-byte header and four-byte payload')


def selected_event_contract(header, event_action, current_action, counter, available_bytes):
    """Selected scalar/extent requirements, not pointer validity or an actual-state assertion.

    The dispatcher itself does not range-check every12-bit ID. Only event40 is used.
    Counter safety is expressed as available bytes rather than a guessed lifetime.
    """
    need(type(header) is int and 0 <= header <= 65535 and header & 4095 == EVENT_ID, 'only selected event40')
    need(all(type(x) is int and 0 <= x <= 65535 for x in (event_action, current_action, counter)), 'u16 fields')
    need(event_action <= current_action, 'real unsigned action guard')
    need(type(available_bytes) is int and available_bytes >= 8 + 4 * counter, 'whole selected payload available')
    return {'slot': TABLE + 4 * EVENT_ID, 'entry': ENTRY, 'payload_offset': 4 + 4 * counter,
            'map_section_byte_offset': 6 + 4 * counter, 'required_event_bytes': 8 + 4 * counter}


def protected_windows(review):
    rows = review['windows']
    need(len(rows) == len(WINDOWS), 'exact minimal window count')
    need([(r['label'], r['address'], r['size']) for r in rows] == [(k, *v) for k, v in WINDOWS.items()], 'closed minimal window roles and geometry')
    return [{k: r[k] for k in ('address', 'size', 'sha256')} for r in rows]


def _regions(raw, inherited, review, sources):
    need(set(review) == {'schema_version', 'required_candidate', 'diagnostic_input', 'source_bindings', 'hit', 'root', 'windows', 'claims'}, 'closed review fields')
    need(review['schema_version'] == 1 and review['required_candidate'] == CANDIDATE and inherited['candidate'] == CANDIDATE, 'fixed current target')
    need(review['claims'] == CLAIMS, 'no unsupported runtime, range or capacity claim')
    root = {'kind': 'actual_quest_log_event_dispatch', 'dispatcher': DISPATCH, 'event_id': EVENT_ID,
            'event_mask': 4095, 'table': TABLE, 'slot': TABLE + 4 * EVENT_ID, 'entry': ENTRY,
            'synchronous_indirect_consumer': 0x081C7ACC, 'instruction_typing_only': True}
    need(review['root'] == root, 'actual finite runtime table root, not a symbol or unrooted decode')
    original = [h for h in inherited['hits'] if h['address'] == HIT]
    need(len(original) == 1 and original[0] == review['hit'] and not original[0]['accepted'] and not original[0]['owner_candidates'], 'one exact inherited external unknown')
    need(original[0]['size'] == 4 and original[0]['kind'] == 'ALL_BYTE_START_U32_ALL_ROM_MIRRORS', 'original all-byte-start hit')
    d.signed(raw, original[0])
    sources_bind(review, sources)
    d.signed(raw, protected_windows(review))
    semantic_consumers(raw)
    window = next(r for r in review['windows'] if r['label'] == 'hit_instruction_window')
    source = {k: window[k] for k in ('address', 'size', 'sha256')}
    evidence = dict(root=root, instruction_window=source,
                    instructions=[{'address': 0x081161EA, 'size': 4}, {'address': 0x081161EE, 'size': 2}],
                    root_verified=True, literal_pool_included=False, **{k:v for k,v in CLAIMS.items() if k != 'literal_pool_included'},
                    local_payload_formula='event + 4 + (8 - 4) * u16_repeat_counter',
                    input_contract='non-null readable event40 header; action<=current action; enough payload bytes; valid nonalias ABI stack',
                    asynchronous_lifetime_edge=False)
    regions = [d.TypedRegion(source['address'], source['address'] + source['size'], KIND, evidence)]
    return regions, dict(status='PASS_ONE_DIRECT_QUEST_LOG_CODE_ROLE', count=1, hit=HIT,
                         protected_windows=len(WINDOWS), protected_bytes=sum(n for _, n in WINDOWS.values()),
                         source_bindings=SOURCE_IDS, **CLAIMS)


def regions(raw, inherited, review, sources, root=None):
    need(identity(raw) == inherited['candidate'] == CANDIDATE, 'current whole candidate mandatory')
    return _regions(raw, inherited, review, sources)
