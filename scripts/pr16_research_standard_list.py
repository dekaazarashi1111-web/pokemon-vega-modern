#!/usr/bin/env python3
"""c3971e83専用・受付標準リスト層。旧recipe/数値層は改作しない。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import pr16_research_counter_numeric as numeric
ROOT = Path(__file__).resolve().parents[1]
PARENT = numeric.CANDIDATE
BASE, WINDOW = 0x09F4A800, 0x800
EVENT = BASE + 0x600
POINTER = 0x09413BAC
SOURCE = 'tools/pr16_research_standard_list.c'
MODEL = 'content/research_economy_v1/canonical_model.json'
ROW_TEXT = ('ポイントとランク', 'ポイントのあつめかた', 'おわる')
API = {'SL_CreateTask':0x08076BB5, 'SL_DestroyTask':0x08076CA1,
       'SL_AddWindow':0x08003CB1, 'SL_RemoveWindow':0x08003E09,
       'SL_CopyWindow':0x08003EED, 'SL_PutWindow':0x08003F6D,
       'SL_FillWindow':0x08004429, 'SL_Print':0x08002C45,
       'SL_Schedule':0x080F77FD, 'SL_DrawFrame':0x080F7F7D,
       'SL_ClearFrame':0x080F7FFD, 'SL_BaseTile':0x080F89CD,
       'SL_Cursor':0x0811030D, 'SL_Input':0x08110BF9,
       'SL_Sound':0x08071A71, 'SL_Suspend':0x08069201, 'SL_Resume':0x080693F5}
need, identity = numeric.need, numeric.identity


def rows(model=None):
    """固定canonicalの日本語/byte対応から生成し、未知字を推定しない。"""
    if model is None: model = json.loads((ROOT/MODEL).read_bytes())
    glyphs = {}
    for row in model['dialogue']:
        text = row['text'].replace('\\n', '\n')
        raw = bytes.fromhex(row['encoded_hex'])
        need(len(raw) == len(text)+1 and raw[-1] == 255, 'single-byte canonical glyph source')
        for char, value in zip(text, raw[:-1]):
            need(char not in glyphs or glyphs[char] == value, 'unambiguous canonical glyph')
            glyphs[char] = value
    try: return tuple(bytes(glyphs[c] for c in text)+b'\xff' for text in ROW_TEXT)
    except KeyError as exc: raise ValueError('unknown canonical glyph') from exc


def header():
    values = rows()
    lines = ['/* 固定canonical文言から生成。手書きglyph IDなし。 */']
    for i, raw in enumerate(values):
        lines.append('static const u8 SL_ROW_%d[] = {%s};' % (i, ','.join(str(x) for x in raw)))
    lines.append('static const u8 * const SL_ROWS[3] = {SL_ROW_0,SL_ROW_1,SL_ROW_2};')
    return '\n'.join(lines)+'\n'


def event(open_address):
    need(type(open_address) is int and BASE <= (open_address & ~1) < EVENT and open_address & 1, 'Thumb entry within code partition')
    code = bytearray(b'\x6a\x5a'); labels = {}; fixes = []
    def ptr(v): code.extend(struct.pack('<I', v))
    def label(name): labels[name] = EVENT + len(code)
    def jump(name): code.append(5); fixes.append((len(code), name)); ptr(0)
    def branch(value, name):
        code.extend(b'\x21\x0d\x80'+struct.pack('<H',value)+b'\x06\x01')
        fixes.append((len(code),name)); ptr(0)
    def call(addr): code.append(0x23); ptr(addr)
    def message(addr): code.extend(b'\x0f\x00'); ptr(addr); code.extend(b'\x09\x04')
    def clear(): code.extend(b'\x16\x0d\x80\0\0')
    def finish(): code.extend(b'\x6c\x02')
    message(0x093C003D); call(0x093BE8A1)
    branch(0, 'menu'); branch(4, 'cap'); branch(13, 'save_fail'); jump('end')
    label('menu'); call(open_address); branch(0xffff, 'wait'); jump('end')
    label('wait'); code.append(0x27)
    branch(0, 'balance'); branch(1, 'guide'); branch(2, 'cancel'); jump('end')
    label('balance'); call(0x093BE033); code.extend(b'\x83\0\x0d\x80')
    call(0x093BE057); code.extend(b'\x83\x01\x0d\x80'); clear(); message(numeric.TEXT); jump('menu')
    label('guide'); clear(); message(0x093C005A); message(0x093C006D); jump('menu')
    label('cancel'); clear(); message(0x093C008E); finish()
    label('cap'); message(0x093C007E); finish()
    label('save_fail'); message(0x093C009E); finish()
    label('end'); finish()
    for at, name in fixes: struct.pack_into('<I', code, at, labels[name])
    need(len(code) <= BASE+WINDOW-EVENT, 'bounded event partition')
    return bytes(code), labels


def audit(parent):
    need(type(parent) is bytes and identity(parent) == PARENT, 'exact accepted numeric parent')
    off = BASE-0x08000000
    need(parent[off:off+WINDOW] == b'\xff'*WINDOW, 'erased scoped allocation')
    need(parent[POINTER-0x08000000:POINTER-0x08000000+4] == struct.pack('<I',numeric.SCRIPT), 'actual local4 script pointer')
    old, _ = numeric.script()
    need(parent[numeric.SCRIPT-0x08000000:numeric.SCRIPT-0x08000000+len(old)] == old, 'accepted numeric event untouched')
    need(parent[numeric.TEXT-0x08000000:numeric.TEXT-0x08000000+15] == numeric.TEXT_AFTER, 'accepted numeric text untouched')
    # 任意byte位置のLE pointer候補も排除。FFだけを未使用の証明としない。
    refs = []
    for match in re.finditer(b'\xf4\x09', parent):
        at = match.start()-2
        if at >= 0:
            value = int.from_bytes(parent[at:at+4], 'little')
            if BASE <= value < BASE+WINDOW: refs.append(at)
    need(not refs, 'no existing absolute reference into allocation')
    stats = int.from_bytes(parent[0x1bc:0x1c0], 'little')
    need(not (stats < BASE+WINDOW and BASE < stats+1671*32), 'outside actual 1671-slot base-stats table')
    return {'base':BASE,'size':WINDOW,'preimage':identity(b'\xff'*WINDOW),
            'absolute_reference_candidates':refs,'base_stats_address':stats,
            'policy':'EXACT_PARENT_POST_BUILD_SCOPED_RESERVATION_NOT_GENERAL_FREE_SPACE',
            'engine_heads':{name:identity(parent[(addr&~1)-0x08000000:(addr&~1)-0x08000000+32]) for name,addr in API.items()}}


def compile_code(out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    compiler = subprocess.check_output(['arm-none-eabi-gcc','-dumpfullversion'], text=True).strip()
    need(compiler == '13.2.1', 'fixed ARM compiler 13.2.1')
    (out/'pr16_research_standard_list_rows.h').write_text(header(), encoding='utf-8')
    ld = ('SECTIONS { . = 0x%X; .text : { KEEP(*(.text.SL_Open)) *(.text*) *(.rodata*) } '
          '.data : { *(.data*) } .bss : { *(.bss*) *(COMMON) } '
          '/DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) } }\n' % BASE)
    ld += '\n'.join('%s = 0x%X;' % (name,address) for name,address in API.items())+'\n'
    (out/'link.ld').write_text(ld)
    command = ['arm-none-eabi-gcc','-mcpu=arm7tdmi','-mthumb','-Os','-ffreestanding','-fno-builtin',
               '-fno-common','-ffunction-sections','-fdata-sections','-fno-unwind-tables','-fno-asynchronous-unwind-tables',
               '-Wall','-Wextra','-Werror','-nostdlib','-I'+str(out),str(ROOT/SOURCE),
               '-Wl,-T,'+str(out/'link.ld'),'-Wl,--gc-sections','-Wl,-e,SL_Open','-o',str(out/'menu.elf')]
    proc = subprocess.run(command,capture_output=True)
    (out/'compile.stdout.txt').write_bytes(proc.stdout); (out/'compile.stderr.txt').write_bytes(proc.stderr)
    need(proc.returncode == 0 and not proc.stderr, 'strict isolated ARM compile')
    symbols = subprocess.check_output(['arm-none-eabi-nm','-n',str(out/'menu.elf')],text=True)
    need(not re.search(r'\s[BbDdCc]\s', symbols), 'no mutable or common allocation')
    resolved = {line.split()[-1]:int(line.split()[0],16) for line in symbols.splitlines() if len(line.split())==3}
    need(resolved['SL_Open'] == BASE, 'bound entry address')
    subprocess.run(['arm-none-eabi-objcopy','-O','binary',str(out/'menu.elf'),str(out/'menu.bin')],check=True)
    code = (out/'menu.bin').read_bytes(); need(0 < len(code) <= EVENT-BASE, 'isolated code partition')
    return code, {'compiler':compiler,'code':identity(code),'open':resolved['SL_Open']|1,
                  'task':resolved['SL_Task']|1,'symbols':symbols,'source':identity((ROOT/SOURCE).read_bytes()),
                  'rows':list(zip(ROW_TEXT,[b.hex() for b in rows()])),'new_arm_compiles':1}


def apply(parent, code, build):
    allocation = audit(parent)
    need(type(code) is bytes and 0 < len(code) <= EVENT-BASE and identity(code)==build['code'], 'bound compiled code')
    need(build['open'] == BASE|1 and BASE <= (build['task']&~1) < BASE+len(code), 'local compiled entries')
    ev, labels = event(build['open'])
    arena = bytearray(b'\xff'*WINDOW); arena[:len(code)] = code; arena[EVENT-BASE:EVENT-BASE+len(ev)] = ev
    patches = [(BASE-0x08000000,b'\xff'*WINDOW,bytes(arena)),
               (POINTER-0x08000000,struct.pack('<I',numeric.SCRIPT),struct.pack('<I',EVENT))]
    result = bytearray(parent)
    for off,before,after in patches:
        need(result[off:off+len(before)]==before and len(before)==len(after),'exact patch preimage')
        result[off:off+len(before)] = after
    undo = bytearray(result)
    for off,before,after in patches: undo[off:off+len(after)] = before
    need(bytes(undo)==parent, 'whole-ROM rollback and outside declaration invariant')
    return bytes(result), {'schema_version':1,'parent':PARENT,'candidate':identity(result),
        'scope':'COUNTER_STANDARD_LIST_ONLY','allocation':allocation,'build':build,'event_labels':labels,
        'patches':[{'offset':o,'before':a.hex(),'after':b.hex()} for o,a,b in patches],
        'declared_bytes':WINDOW+4,'changed_bytes':sum(a!=b for a,b in zip(parent,result)),
        'outside_declared_changes':0,'new_ewram_bytes':0,'old_numeric_bytes_unchanged':True,
        'natural_earning_spending_accepted':False,'release_ready':False,'active_baseline_changed':False}
