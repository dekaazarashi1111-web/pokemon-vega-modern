#!/usr/bin/env python3
"""JP候補2組の有限現物観測。型受入・自然到達・donor移管を行わない。"""
from __future__ import annotations
import collections
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import pr16_dex_hof_jp_crosswalk_candidates as cross
from pr16_dex_hof_space_assets import decode

need, identity = cross.need, cross.identity
BASE = 0x08000000
CANDIDATE = dict(size=33554432, sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
# 独立の探索予算。英語reference size/JP extentではなく、越境は明示停止する。
FUNCTIONS = {
    'CursorCB_FieldMove': (0x08124F08, 0x300),
    'CursorCB_Enter': (0x08124930, 0x180),
    'DisplaySwitchedHeldItemMessage': (0x08120D48, 0x100),
    'TryGiveMailToSelectedMon': (0x08127D3C, 0x180),
    'Task_SwitchItemsYesNo': (0x081240D8, 0x80),
    'Task_HandleSwitchItemsYesNoInput': (0x0812410C, 0x180),
    'ChooseMonToGiveMailFromMailbox': (0x08127D10, 0x60),
    'Task_HandleChooseMonInput': (0x08120318, 0x100),
    'HandleChooseMonSelection': (0x081203B4, 0x200),
    'Task_HandleSelectionMenuInput': (0x08123438, 0x180),
    'DisplayPartyMenuMessage': (0x08120AE8, 0x60),
    'PartyMenuPrintText': (0x0812278C, 0x80),
    'StringExpandPlaceholders': (0x08008B48, 0x180),
    'AddTextPrinterParameterized2': (0x080F7D28, 0x100),
}
TEXTS = (
    ('gText_CantUseUntilNewBadge', 0x083DDEC6),
    ('gText_NoMoreThanThreeMayEnter', 0x083DDEE4),
    ('gText_SwitchedPkmnItem', 0x083DE016),
    ('gText_PkmnHoldingItemCantHoldMail', 0x083DE02E),
)
CELLS = (('ENTER', 0x08419E0C, 0x08124931), ('FIELD_MOVES_FIRST', 0x08419E3C, 0x08124F09))
HITS = (0x083DDEE1, 0x083DE02B)
MAX_TEXT = 128
# 同じ固定pretの公開charmapに存在する限定serializer。未対応controlは拒否する。
CONTROL = {0xFE: ('newline', 1), 0xFB: ('paragraph', 1), 0xFA: ('scroll', 1)}
EXT = {9: ('pause_until_press', 2)}
EXTRA = {'charmap.txt': {'size': 21853, 'sha256': '4da662317b3b5109a52064f9012d85b644d1dbf0f3f24243374aeef4cf25f061', 'git_blob_sha': 'b9d0ed9de00d05fc303bb987a5aa634b19009b47'}, 'include/characters.h': {'size': 12798, 'sha256': '6787db76f83c4f8426c5adbfa7aa061c46585db9522f1fef00ad888616199b98', 'git_blob_sha': 'd00ecf0a3afcd9fc1fa9534c00f4b74793d5f06f'}, 'src/string_util.c': {'size': 14320, 'sha256': 'ed9519d4eaf51ed660a522915366dc0ebf2916d592a91a1d7fc2a012e4f3f17e', 'git_blob_sha': '5c26d151a61274caac3a16c3b9c4eb73bf9a9e26'}, 'src/text.c': {'size': 63210, 'sha256': '5696f49443eeaaac74b530421ac7f0cbfc71996c557399583788111c322dd80c', 'git_blob_sha': 'f3eef07ce6dea8269980a5ecfdd6902c1c9c13d2'}}


def chunk(raw, address, size):
    need(type(raw) is bytes and type(address) is int and type(size) is int and size > 0
         and 0 <= address-BASE <= len(raw)-size, '有限ROM窓の境界')
    return raw[address-BASE:address-BASE+size]


def u32(raw, address):
    return int.from_bytes(chunk(raw, address, 4), 'little')


def span(raw, address, size):
    return dict(address=address, **identity(chunk(raw, address, size)))


def lexical_text(raw, start, limit=MAX_TEXT):
    """未対応制御を拒否し、payload非公開でEOS位置を測る。実printer読取の証明ではない。"""
    need(type(limit) is int and 0 < limit <= MAX_TEXT, '独立した有限text予算')
    pos = 0; tokens = []
    while pos < limit:
        value = chunk(raw, start+pos, 1)[0]
        if value == 0xFF:
            tokens.append(dict(offset=pos, size=1, role='eos'))
            return dict(**span(raw, start, pos+1), eos_address=start+pos, tokens=tokens,
                        lexical_complete=True, runtime_read_proven=False)
        if value == 0xFD:
            need(pos+2 <= limit, 'placeholder全operand')
            variable = chunk(raw, start+pos+1, 1)[0]
            need(variable in (2, 3, 4), '固定STR_VARのみ')
            role, size = 'string_var_'+str(variable-1), 2
        elif value == 0xFC:
            need(pos+2 <= limit, 'extended control全selector')
            selector = chunk(raw, start+pos+1, 1)[0]
            need(selector in EXT, '未対応extended controlは拒否')
            role, size = EXT[selector]
        elif value in CONTROL:
            role, size = CONTROL[value]
        else:
            need(value < 0xF7, '未知special glyph/controlは拒否')
            role, size = 'glyph', 1
        need(pos+size <= limit, 'tokenは窓内で完結')
        if role == 'glyph' and tokens and tokens[-1]['role'] == 'glyph':
            tokens[-1]['size'] += size
        else:
            tokens.append(dict(offset=pos, size=size, role=role))
        pos += size
    raise ValueError('EOSは有限窓で未観測')


def named_symbols(value):
    out = {}
    for row in value['mapped_symbols']:
        address = int(row['jp_address'], 16)
        need(address not in out, '異なるsymbolの同住所を拒否')
        out[address] = row['name']
        if row['name'] in FUNCTIONS or row['name'] in ('InitPartyMenu', 'CreateTask', 'Task_PrintAndWaitForText'):
            out[address | 1] = row['name']+'(Thumb)'
    return out


def observe_cfg(raw, entry, budget, names):
    """entryから直接CFGのみ。BL外部は追跡せず、BX/PC write/予算外を明示停止。"""
    need(type(budget) is int and 2 <= budget <= 0x400 and budget % 2 == 0 and entry % 2 == 0, '有限Thumb予算')
    todo = [entry]; instructions = {}; extents = {}; edges = []; literals = []; stops = []; covered = {}
    while todo:
        address = todo.pop()
        if address in instructions: continue
        if not entry <= address < entry+budget:
            stops.append(dict(address=address, reason='budget_exit')); continue
        if address in covered:
            stops.append(dict(address=address, reason='overlapping_instruction')); continue
        first = int.from_bytes(chunk(raw, address, 2), 'little')
        size = 4 if first & 0xF800 == 0xF000 else 2
        if address+size > entry+budget:
            stops.append(dict(address=address, reason='truncated_instruction')); continue
        try:
            rows = decode(raw, address, size)
        except ValueError:
            stops.append(dict(address=address, reason='unsupported_instruction')); continue
        need(len(rows) == 1, '完全な命令を1つだけ')
        op = rows[0][1]; kind = op[0]
        if any(address+i in covered for i in range(size)):
            stops.append(dict(address=address, reason='overlapping_instruction')); continue
        for i in range(size): covered[address+i] = address
        instructions[address] = op; extents[address] = size
        if kind == 'ldr_literal':
            cell = op[2]; value = u32(raw, cell)
            # 名前付き住所/Thumb code pointerのみ。任意literal値/ROM断片は出さない。
            item = dict(instruction=address, register=op[1], cell=span(raw, cell, 4), named_target=names.get(value))
            if value in names: item['target'] = value
            literals.append(item)
        if kind == 'bl':
            edges.append(dict(callsite=address, target=op[1], target_name=names.get(op[1]), return_assumed=False))
            todo.append(address+size)
        elif kind == 'b': todo.append(op[1])
        elif kind == 'b_cond': todo.extend((op[2], address+size))
        elif kind == 'bx' or (kind == 'pop' and 15 in op[1]) or (kind in ('mov_high', 'add_high') and op[1] == 15):
            stop = dict(address=address, reason='indirect_or_return')
            # 既知のentry LDR/BX hookだけ検出し、飛先を実行・追跡しない。
            previous = instructions.get(address-2)
            if kind == 'bx' and previous and previous[0] == 'ldr_literal' and previous[1] == op[1]:
                value = u32(raw, previous[2])
                if value & 1 and BASE <= (value & ~1) < BASE+len(raw):
                    stop.update(reason='literal_thumb_hook', target=value, cell=previous[2])
            stops.append(stop)
        else: todo.append(address+size)
    windows = []
    for address in sorted(extents):
        size = extents[address]
        if windows and windows[-1][0]+windows[-1][1] == address: windows[-1][1] += size
        else: windows.append([address, size])
    return dict(entry=entry, exploration_budget=budget, instruction_count=len(instructions),
                windows=[span(raw, a, n) for a, n in windows], calls=sorted(edges, key=lambda r:r['callsite']),
                named_literal_reads=sorted(literals, key=lambda r:r['instruction']), stops=sorted(stops,key=lambda r:r['address']),
                path_feasibility_proven=False, api_arguments_proven=False, registered_root_proven=False)


def measure(raw, contract_value):
    need(identity(raw) == CANDIDATE, '現候補全ROM identity')
    names = named_symbols(contract_value)
    functions = {name: observe_cfg(raw, a, n, names) for name, (a, n) in FUNCTIONS.items()}
    texts = {name: lexical_text(raw, a) for name, a in TEXTS}
    cells = [dict(name=name, **span(raw, a, 4), expected_thumb=expected,
                  matches_expected=u32(raw, a) == expected,
                  actual_thumb_target=(u32(raw,a) if u32(raw,a) & 1 and BASE <= (u32(raw,a) & ~1) < BASE+len(raw) else None)) for name, a, expected in CELLS]
    hit_roles = []
    for hit in HITS:
        roles = []
        for address in range(hit, hit+4):
            owners = [(name, row, token) for name, row in texts.items() for token in row['tokens']
                      if row['address']+token['offset'] <= address < row['address']+token['offset']+token['size']]
            roles.append(dict(address=address, owners=[dict(text=name, role=t['role']) for name,r,t in owners]))
        hit_roles.append(dict(**span(raw, hit, 4), byte_roles=roles, accepted=False))
    return dict(status='MEASURED_CURRENT_JP_CANDIDATES_NOT_TYPE_ACCEPTANCE', candidate=CANDIDATE,
                functions=functions, texts=texts, cells=cells, hits=hit_roles,
                classified=779, unclassified=95, newly_classified=0, native_processes=0,
                formal_rom_changed=False, formal_save_changed=False, donor_eligible=False,
                serializer_execution_proven=False, all_api_arguments_proven=False,
                old_full_rom_scan_runs=0)


def validate_report(value):
    need(type(value) is dict and set(value) in (REPORT_FIELDS, REPORT_FIELDS|MEASURED_FIELDS), '閉じたreport schema')
    need(value['status'] == 'MEASURED_CURRENT_JP_CANDIDATES_NOT_TYPE_ACCEPTANCE', '診断statusのみ')
    need(value['candidate'] == CANDIDATE and tuple(value['functions']) == tuple(FUNCTIONS) and tuple(value['texts']) == tuple(n for n,a in TEXTS), '閉じた候補と根')
    for field in ('newly_classified', 'native_processes', 'old_full_rom_scan_runs'):
        need(type(value[field]) is int and value[field] == 0, '未実行・未受入counter '+field)
    need(value['classified'] == 779 and value['unclassified'] == 95, '旧分類不変')
    for field in ('formal_rom_changed', 'formal_save_changed', 'donor_eligible', 'serializer_execution_proven', 'all_api_arguments_proven'):
        need(value[field] is False, '未証明claim '+field)
    for name,row in value['texts'].items():
        expected = dict(TEXTS)[name]
        need(set(row) == {'address','size','sha256','eos_address','tokens','lexical_complete','runtime_read_proven'}, '閉じたtext schema')
        need(type(row['size']) is int and type(row['eos_address']) is int and row['address'] == expected and 1 <= row['size'] <= MAX_TEXT and row['eos_address'] == expected+row['size']-1, '観測text geometry')
        need(re.fullmatch('[0-9a-f]{64}', row['sha256']) and row['runtime_read_proven'] is False and row['lexical_complete'] is True, '字句/EOSとruntimeを分離')
        offset = 0
        for token in row['tokens']:
            need(set(token) == {'offset','size','role'} and token['offset'] == offset and type(token['size']) is int and token['size'] > 0, 'payloadを持たない連続token')
            need(token['role'] in {'glyph','newline','paragraph','scroll','pause_until_press','string_var_1','string_var_2','string_var_3','eos'}, '限定token種別')
            if token['role'] != 'glyph': need(token['size'] == (2 if token['role'].startswith('string_var_') or token['role'] == 'pause_until_press' else 1), '制御arity')
            offset += token['size']
        need(offset == row['size'] and row['tokens'][-1]['role'] == 'eos' and sum(t['role'] == 'eos' for t in row['tokens']) == 1, '唯一の完全EOS')
    need(len(value['cells']) == 2 and len(value['hits']) == 2 and all(r['accepted'] is False for r in value['hits']), '有限2組は未受入')
    validate_structure(value)
    return True


REPORT_FIELDS = {'status','candidate','functions','texts','cells','hits','classified','unclassified','newly_classified','native_processes','formal_rom_changed','formal_save_changed','donor_eligible','serializer_execution_proven','all_api_arguments_proven','old_full_rom_scan_runs'}
MEASURED_FIELDS = {'source_head','run_id','current_rom_reconstructions','unit_tests','current_owner_count','source_bindings','fixed_crosswalk_identity','extra_source_bindings'}


def valid_span(row):
    need(type(row) is dict and set(row) == {'address','size','sha256'}, '閉じたaddress-size-SHA')
    need(type(row['address']) is int and type(row['size']) is int and row['size'] > 0
         and BASE <= row['address'] <= BASE+CANDIDATE['size']-row['size']
         and type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}',row['sha256']), '正規ROM窓identity')


def validate_structure(value):
    names = set(FUNCTIONS)|{'InitPartyMenu','CreateTask','Task_PrintAndWaitForText'}|{n for n,a in TEXTS}|{'sCursorOptions','TryEnterMonForMinigame','CancelParticipationPrompt','Task_SwitchHoldItemsPrompt','Task_DisplayGaveMailFromPartyMessage','Task_DisplayGaveMailFromBagMessage','Task_HandleSwitchItemsFromBagYesNoInput','gText_PkmnCantParticipate','gText_CancelParticipation'}
    names |= {name+'(Thumb)' for name in names}
    for name,row in value['functions'].items():
        need(set(row) == {'entry','exploration_budget','instruction_count','windows','calls','named_literal_reads','stops','path_feasibility_proven','api_arguments_proven','registered_root_proven'}, '閉じた関数schema')
        need((row['entry'],row['exploration_budget']) == FUNCTIONS[name] and type(row['instruction_count']) is int and 0 <= row['instruction_count'] <= row['exploration_budget']//2, '固定関数予算')
        need(all(row[k] is False for k in ('path_feasibility_proven','api_arguments_proven','registered_root_proven')), 'CFGを実consumer証明に昇格しない')
        for window in row['windows']:
            valid_span(window)
            need(row['entry'] <= window['address'] and window['address']+window['size'] <= row['entry']+row['exploration_budget'], '探索窓内')
        for call in row['calls']:
            need(set(call) == {'callsite','target','target_name','return_assumed'} and call['return_assumed'] is False and (call['target_name'] is None or call['target_name'] in names), '閉じたBL観測')
            need(all(type(call[k]) is int and BASE <= call[k] < BASE+CANDIDATE['size'] for k in ('callsite','target')), 'call ROM住所のみ')
        for literal in row['named_literal_reads']:
            need(set(literal) == ({'instruction','register','cell','named_target','target'} if literal['named_target'] is not None else {'instruction','register','cell','named_target'}), '未知literal payload拒否')
            valid_span(literal['cell'])
            need(type(literal['register']) is int and 0 <= literal['register'] < 8 and type(literal['instruction']) is int, 'LDR operand geometry')
            need(literal['named_target'] is None or literal['named_target'] in names, '名前付きliteralのみ')
            if 'target' in literal: need(type(literal['target']) is int and BASE <= literal['target'] < BASE+CANDIDATE['size'], '名前付きROM住所')
        for stop in row['stops']:
            need(set(stop) == ({'address','reason','target','cell'} if stop['reason'] == 'literal_thumb_hook' else {'address','reason'}), '閉じたCFG停止')
            need(type(stop['address']) is int and stop['reason'] in {'budget_exit','overlapping_instruction','truncated_instruction','unsupported_instruction','indirect_or_return','literal_thumb_hook'}, '固定停止reason')
            if stop['reason'] == 'literal_thumb_hook': need(type(stop['target']) is int and stop['target'] & 1 and BASE <= stop['target'] < BASE+CANDIDATE['size'] and type(stop['cell']) is int, 'Thumb hook住所')
    for row,(name,address,expected) in zip(value['cells'],CELLS):
        need(set(row) == {'name','address','size','sha256','expected_thumb','matches_expected','actual_thumb_target'} and (row['name'],row['address'],row['size'],row['expected_thumb']) == (name,address,4,expected), '閉じた2登録cell')
        valid_span({k:row[k]for k in ('address','size','sha256')})
        target=row['actual_thumb_target']
        need(target is None or type(target) is int and target & 1 and BASE <= target < BASE+CANDIDATE['size'], '観測Thumb pointerのみ')
        need(type(row['matches_expected']) is bool and row['matches_expected'] is (target == expected), '一致flagとtarget同一')
    for row,address in zip(value['hits'],HITS):
        need(set(row) == {'address','size','sha256','byte_roles','accepted'} and row['address'] == address and row['size'] == 4, '閉じたheld4byte')
        valid_span({k:row[k]for k in ('address','size','sha256')})
        need(len(row['byte_roles']) == 4, '全4byte役割')
        for j,byte in enumerate(row['byte_roles']):
            need(set(byte) == {'address','owners'} and byte['address'] == address+j, '閉じた1byte役割')
            expected=[]
            for name,text in value['texts'].items():
                for token in text['tokens']:
                    if text['address']+token['offset'] <= address+j < text['address']+token['offset']+token['size']:
                        expected.append(dict(text=name,role=token['role']))
            need(byte['owners'] == expected, '実token geometryへ正確にjoin')
    if set(value) == REPORT_FIELDS|MEASURED_FIELDS:
        need(type(value['source_head']) is str and re.fullmatch('[0-9a-f]{40}',value['source_head']) and type(value['run_id']) is int and value['run_id'] > 0, '正規source/run')
        need(value['current_rom_reconstructions'] == 1 and value['current_owner_count'] == 115 and type(value['unit_tests']) is int and value['unit_tests'] > 0, '有限実測counter')
        need(value['fixed_crosswalk_identity'] == cross.CONTRACT_ID and value['extra_source_bindings'] == EXTRA, '独立source同一')
        import pr16_dex_hof_jp_consumer_probe_actions as actions
        need(value['source_bindings'] == {name:identity((ROOT/name).read_bytes()) for name in sorted(actions.CODE)}, '実行された全source bytes')
