#!/usr/bin/env python3
"""正本Cの初期化・ショップcallbackを変更せず抽出する限定host検証。

engine/Flash/描画は明示したstub。通常new-game/実取引native受入ではない。
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'overlays/research_economy_v1/research_economy_v1.c'
SOURCE_BLOB = '888ea10e6fa008b4c7fdbbb7e5a302252bc2fadb'
FUNCTIONS = (
    'read_u16', 'write_u16', 'write_u32', 'clear_bytes', 'bytes_are_zero',
    'initialize_owner_at', 'reset_volatile_state', 'ensure_volatile_state',
    'set_result', 'ResearchEconomy_SaveChecksum', 'ResearchEconomy_SaveFinalize',
    'ResearchEconomy_SaveInitNew', 'close_window', 'page_row_count',
    'append_balance_text', 'render_menu', 'finish_menu', 'Task_HandleResearchShop',
    'ResearchEconomy_OpenShop', 'ResearchEconomy_PostShopMenu',
    'ResearchEconomy_PurchaseSelected',
)

def need(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)

def blob(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def section(text: str, start: str, end: str) -> str:
    need(text.count(start) == text.count(end) == 1, 'unique declaration boundaries')
    a, b = text.index(start), text.index(end)
    need(a < b, 'ordered declaration boundaries')
    return text[a:b]

def function(text: str, name: str) -> str:
    matches = list(re.finditer(r'^(?:static )?(?:void|u8|u16|u32) ' + re.escape(name) + r'\([^;]*?\)\n\{', text, re.M))
    need(len(matches) == 1, 'one canonical function: ' + name)
    a = matches[0].start()
    b = text.find('\n}\n', matches[0].end())
    need(b >= 0, 'closed canonical function: ' + name)
    return text[a:b + 3]

def generate(text: str) -> tuple[str, dict]:
    need(blob(text.encode()) == SOURCE_BLOB, 'canonical source blob changed; audit required')
    declarations = section(text, 'typedef uint8_t u8;', '/* The build must supply')
    declarations += section(text, 'enum {\n    LEDGER_MAGIC', '_Static_assert(sizeof(struct Task)')
    bodies = [function(text, name) for name in FUNCTIONS]
    prefix = '#include <assert.h>\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <stdint.h>\n#include "overlays/research_economy_v1/research_economy_v1.h"\n#define RESEARCH_ECONOMY_SHOP_COUNT 23u\n#define RESEARCH_ECONOMY_RANK_COUNT 7u\n'
    shim = (ROOT / 'tools/research_ui_boundary_shim.c').read_text()
    need(shim.count('/* CANONICAL_FUNCTIONS */') == 1, 'one canonical insertion')
    generated = prefix + declarations + shim.replace('/* CANONICAL_FUNCTIONS */', '\n'.join(bodies))
    return generated, {name: hashlib.sha256(body.encode()).hexdigest() for name, body in zip(FUNCTIONS, bodies)}
