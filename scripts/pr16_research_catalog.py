#!/usr/bin/env python3
"""Research全catalogの読取専用監査。実購入/旧受入/ARM buildは実行しない。"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'content/research_economy_v1/canonical_model.json'
ITEMS = 'manifests/item_ids.csv'
C = 'tools/mgba_pr16_research_catalog.c'
CANDIDATE = {'size': 33554432, 'sha256': '5d1fc9c47225ae8c0a369514b899a062af3699fa3c9a2f617e94ffd5f7dcc1ab'}
TABLE = 0x093BF9EC
UNLOCKS = ('VEGA_DH_CLEAR','KANTO_EARLY_ACCESS','VEGA_BADGE_1','KANTO_DAYCARE_QUEST',
           'VEGA_BADGE_5','VEGA_BADGE_6','COMPETITIVE_SUPPLY_UNLOCKED','VEGA_BADGE_7',
           'VEGA_BADGE_8','KANTO_LEAGUE_CLEAR','UB_PARADOX_UNLOCKED','KANTO_CERT_1',
           'KANTO_CERT_2','KANTO_CERT_3','VEGA_HALL_OF_FAME')
DAILY = {'ITEM_KEY_EXP_CANDY_L': 0, 'ITEM_KEY_BOTTLE_CAP': 1,
         'ITEM_KEY_EXP_CANDY_XL': 2, 'ITEM_KEY_GOLD_BOTTLE_CAP': 3}
CASE = 'catalog-all-pages-readonly'

def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def identity(raw: bytes) -> dict:
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def integer(value, low: int, high: int) -> int:
    need(type(value) is int and low <= value <= high, '整数の範囲/型')
    return value

def load(raw: bytes):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'JSON重複key')
            result[key] = value
        return result
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda _: need(False, '非有限JSON'))

def exact(actual, expected) -> bool:
    return json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True)

def encoded(value: str) -> bytes:
    need(type(value) is str and 2 <= len(value) <= 512 and len(value) % 2 == 0,
         '有界の符号列')
    need(all(c in '0123456789abcdef' for c in value), '正規hex')
    result = bytes.fromhex(value)
    need(result[-1] == 255 and 255 not in result[:-1], '終端は末尾一個だけ')
    return result

def span(rom: bytes, address: int, size: int) -> bytes:
    integer(address, 0x08000000, 0x09FFFFFF)
    integer(size, 1, 4096)
    offset = address - 0x08000000
    need(offset + size <= len(rom), 'ROM pointer範囲')
    return rom[offset:offset + size]

def audit_tables(rom: bytes, model: dict, item_csv: str) -> dict:
    """合成ROMにも使える意味検査。本番入口auditは別途full SHAを固定する。"""
    need(model['schema_version'] == 1 and type(model['schema_version']) is int
         and model['status'] == 'PASS' and model['task'] == 'T23', '正本schema')
    shop, dialogues = model['shop'], model['dialogue']
    need(len(shop) == 23 and len(dialogues) == 35, '全23商品/35文言')
    inventory = list(csv.DictReader(io.StringIO(item_csv)))
    items = {r['item_key']: r for r in inventory}
    need(len(items) == len(inventory), 'manifest重複key')
    seen_keys, seen_items, rows = set(), set(), []
    encoding_map = {}
    def text_consistency(text, data):
        # これはcanonical符号列の内部整合性。独立charmap受入とは呼ばない。
        text = text.replace('\\n', '\n')
        need(len(text) + 1 == len(data), '本文と符号列の長さ')
        for char, value in zip(text, data[:-1]):
            need(char not in encoding_map or encoding_map[char] == value,
                 '同一文字の符号が不一致')
            encoding_map[char] = value
    for index, row in enumerate(shop):
        need(integer(row['index'], 0, 22) == index, 'catalog順序')
        key, item = row['shop_entry_key'], row['item_key']
        need(key not in seen_keys and item not in seen_items, 'catalog重複')
        seen_keys.add(key); seen_items.add(item)
        item_id = integer(row['item_id'], 1, 2047)
        price = integer(row['point_cost'], 1, 65535)
        quantity = integer(row['quantity'], 1, 999)
        limit = integer(row['daily_limit'], 0, 255)
        need(item in items and int(items[item]['id']) == item_id
             and items[item]['display_name'] == row['item_display_name'], 'item manifest結合')
        need(row['status'] == 'ACTIVE' and row['repeatability'] == 'REPEATABLE', '商品採用状態')
        need(row['row_text'] == f"{row['item_display_name']} {price}RP", '表示価格/日本語商品名')
        need(row['unlock_key'] in UNLOCKS, '既知の解放条件')
        daily = item in DAILY
        need(row['stock_policy'] == ('DAILY_LIMITED' if daily else 'UNLIMITED_AFTER_UNLOCK')
             and bool(limit) == daily, '在庫policy')
        fields = struct.unpack('<HHHBBBBBBI', span(rom, TABLE + 16 * index, 16))
        expected = (item_id, price, quantity, UNLOCKS.index(row['unlock_key']), int(daily),
                    DAILY.get(item, 255), limit, 255, 0)
        need(fields[:-1] == expected, '実ROM商品ABI ' + str(index))
        data = encoded(row['row_text_hex']); text_consistency(row['row_text'], data)
        need(span(rom, fields[-1], len(data)) == data, '実ROM日本語商品行 ' + str(index))
        rows.append({'index': index, 'key': key, 'item_id': item_id,
                     'name_ja': row['item_display_name'], 'price_rp': price, 'quantity': quantity,
                     'unlock_key': row['unlock_key'], 'daily_limit': limit,
                     'row_text': row['row_text'], 'row_address': fields[-1], 'row_binding': identity(data)})
    seen, text_rows = set(), []
    for row in dialogues:
        key = row['dialogue_key']; need(key not in seen, 'dialogue重複'); seen.add(key)
        data = encoded(row['encoded_hex']); text_consistency(row['text'], data)
        need(span(rom, row['runtime_address'], len(data)) == data, '実ROM文言 ' + key)
        text_rows.append({'key': key, 'text_ja': row['text'], 'address': row['runtime_address'],
                          'binding': identity(data), 'native_display_accepted': False})
    need(len(set(encoding_map.values())) == len(encoding_map), '文字符号の曖昧性')
    return {'status': 'PASS_ROM_CATALOG_AND_DIALOGUE_BYTES', 'shop_rows': rows,
            'dialogues': text_rows, 'shop_count': 23, 'dialogue_count': 35,
            'catalog_binding': identity(span(rom, TABLE, 368)), 'production_changes': 0,
            'natural_progress_accepted': False, 'all_dialogue_native_display_accepted': False}

def audit(rom: bytes) -> dict:
    need(identity(rom) == CANDIDATE, '現在候補full SHA')
    result = audit_tables(rom, load((ROOT / MODEL).read_bytes()), (ROOT / ITEMS).read_text())
    return dict(result, candidate=identity(rom), model_binding=identity((ROOT / MODEL).read_bytes()),
                item_manifest_binding=identity((ROOT / ITEMS).read_bytes()))

def generate(seed: bytes) -> bytes:
    import pr16_research_purchase as previous
    source = previous.generate(seed).decode()
    token = 'int main(int argc,char**argv){'
    need(source.count(token) == 1, '唯一の旧main')
    # 保存済み19商品fixtureを全23表示へ拡張。観測前の正規FlagSetだけ。
    begin = source.index('static struct mCore*up_setup(')
    end = source.index('/* Continue preserves facing.', begin)
    setup = source[begin:end].replace('up_setup(', 'ct_setup(').replace('si_open(', 'ct_open(')
    start_open = source.index('static struct mCore*si_open(')
    end_open = source.index('/* Return UINT32_MAX', start_open)
    opener = source[start_open:end_open].replace('si_open(', 'ct_open(')
    video = 'c->setVideoBuffer(c,si_video,240);si_flash(c);'
    need(opener.count(video) == 1, '起動前のvideo接続点')
    opener = opener.replace(video, 'c->setVideoBuffer(c,si_video,240);c->reset(c);si_flash(c);')
    marker = ' run_key_frames(c,0,2);'
    need(setup.count(marker) == 1, '停止fixtureの単一挿入点')
    setup = setup.replace(marker, marker + '\n (void)call_preserving(c,QOL_FLAG_SET,QOL_FLAG_DH_CLEAR,0,0,0);')
    return (source.replace(token, 'int accepted_purchase_main(int argc,char**argv){')
            + '\n' + opener + '\n' + setup + '\n' + (ROOT / C).read_text()).encode()

def validate_native(raw: bytes) -> dict:
    need(0 < len(raw) < 12000, 'native出力上限')
    rows = [load(line) for line in raw.splitlines()]
    need(len(rows) == 8, 'root/open/5page/result')
    need(exact(rows[0], {'binding':'map98/3-background0','events':0x09413C50,'backgrounds':0x09413C14,
                    'script':0x093C0328,'catalog':0,'item':4,'price':10,'quantity':5}), '実背景root')
    menu = rows[1]
    need(set(menu) == {'shop_open','eligible_count','window','callback','native_tasks'}, 'menu fields')
    need(menu['shop_open'] == 'catalog' and integer(menu['eligible_count'],23,23) == 23
         and integer(menu['native_tasks'],1,1) == 1, '全catalog実task')
    integer(menu['window'],0,31); integer(menu['callback'],0x093BD001,0x093BFFFF)
    last_frame = 899
    for page, event in enumerate(rows[2:7]):
        need(set(event) == {'page','catalog_indices','frame','screen_sha256'}, 'page fields')
        need(integer(event['page'],0,4) == page and event['catalog_indices'] == list(range(page*5,min(23,page*5+5))), '全page順序')
        for i in event['catalog_indices']: integer(i,0,22)
        integer(event['frame'],last_frame + 1,10000); last_frame = event['frame']
        digest = event['screen_sha256']
        need(type(digest) is str and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest), '画面hash')
    need(len({r['screen_sha256'] for r in rows[2:7]}) == 5, '5枚の異なる実画面')
    need(exact(rows[-1], {'status':'PASS','case':CASE,'candidate_sha256':CANDIDATE['sha256'],
                     'catalog_count':23,'pages':5,'fresh_cores':1,'guarded_host_writes':0,
                     'manual_saves':0,'transaction_saves':0,'natural_progress_accepted':False,
                     'purchase_reruns':0,'cancel_reruns':0,'warnings_errors':0}), '限定結果')
    return dict(rows[-1], root=rows[0], menu=menu, screens=rows[2:7], stdout=identity(raw))
