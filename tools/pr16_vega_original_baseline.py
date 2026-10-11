"""Issue19: 原作Vegaだけを読む。現行ROM・混合習得表には書き込まない。"""
from __future__ import annotations

import csv
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import unicodedata
from urllib.parse import urljoin, urlsplit
import zipfile

TASK = 'USER-20260921-LEARNSET-BASELINE-RESET'
INDEX_URL = 'https://w.atwiki.jp/altair1/pages/19.html'
ROM_BASE = 0x08000000
PENDING = 'content/modernization/pr16_learnset_baseline_evidence/vega_original_pending.json'


class SourceError(ValueError):
    """原本の衝突・欠落・範囲外。推測や現行混合表で補完しない。"""


def require(value, message):
    if not value:
        raise SourceError(message)


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def stable(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def text(value):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', value)).strip()


def page_url(value):
    value = urljoin(INDEX_URL, value)
    u = urlsplit(value)
    require(u.scheme == 'https' and u.netloc == 'w.atwiki.jp'
            and re.fullmatch(r'/altair1/pages/[0-9]+\.html', u.path)
            and not u.query and not u.fragment, '許可外のWiki URL')
    return value


class WikiTables(HTMLParser):
    """rowspan/colspanとリンクを捨てずに、HTML表を事実行へ分離する。"""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.stack = []
        self.heading = ''
        self.heading_tag = None
        self.heading_parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.heading_tag, self.heading_parts = tag, []
        if tag == 'table':
            table = {'heading': self.heading, 'rows': []}
            self.tables.append(table)
            self.stack.append({'table': table, 'row': None, 'cell': None, 'link': None})
        if not self.stack:
            return
        ctx = self.stack[-1]
        if tag == 'tr':
            ctx['row'] = []
            ctx['table']['rows'].append(ctx['row'])
        elif tag in ('th', 'td') and ctx['row'] is not None:
            cell = {'text': '', 'links': [], 'rowspan': attrs.get('rowspan', '1'),
                    'colspan': attrs.get('colspan', '1'), 'tag': tag}
            ctx['row'].append(cell)
            ctx['cell'] = cell
        elif tag == 'a' and ctx['cell'] is not None and 'href' in attrs:
            ctx['link'] = {'href': attrs['href'], 'text': ''}
            ctx['cell']['links'].append(ctx['link'])
        elif tag == 'br' and ctx['cell'] is not None:
            ctx['cell']['text'] += '\n'

    def handle_data(self, data):
        if self.heading_tag:
            self.heading_parts.append(data)
        if self.stack:
            ctx = self.stack[-1]
            if ctx['cell'] is not None:
                ctx['cell']['text'] += data
            if ctx['link'] is not None:
                ctx['link']['text'] += data

    def handle_endtag(self, tag):
        if tag == self.heading_tag:
            self.heading = text(''.join(self.heading_parts))
            self.heading_tag = None
        if not self.stack:
            return
        ctx = self.stack[-1]
        if tag == 'table':
            self.stack.pop()
        elif tag in ('th', 'td'):
            ctx['cell'], ctx['link'] = None, None
        elif tag == 'tr':
            ctx['row'], ctx['cell'], ctx['link'] = None, None, None
        elif tag == 'a':
            ctx['link'] = None


def parse_tables(raw):
    parser = WikiTables()
    parser.feed(raw.decode('utf-8'))
    parser.close()
    require(not parser.stack, '閉じていないWiki表')
    return parser.tables


def index_records(tables):
    found = []
    for table in tables:
        rows = table['rows']
        if not rows or 'No.' not in [text(c['text']) for c in rows[0]]:
            continue
        for row in rows[1:]:
            require(len(row) % 2 == 0, '図鑑indexの列数が不正')
            for pos in range(0, len(row), 2):
                number, label = text(row[pos]['text']), row[pos + 1]
                if not number and not text(label['text']):
                    continue
                require(re.fullmatch(r'[0-9]{1,3}', number), '図鑑番号が不正')
                links = label['links']
                require(len(links) == 1 and text(links[0]['text']) == text(label['text']),
                        '図鑑indexの名前/リンクが曖昧')
                found.append({'dex_no': int(number), 'name_ja': text(label['text']),
                              'url': page_url(links[0]['href'])})
    require(found, 'Vega図鑑indexがない')
    for key in ('dex_no', 'name_ja', 'url'):
        require(len({r[key] for r in found}) == len(found), '重複図鑑identity: ' + key)
    return sorted(found, key=lambda r: r['dex_no'])


def join_roster(manifest_raw, pending, index):
    rows = list(csv.DictReader(io.StringIO(manifest_raw.decode('utf-8-sig'))))
    manifests = {r['species_key']: r for r in rows}
    require(len(manifests) == len(rows), 'Species key重複')
    names = {r['name_ja']: r for r in index}
    require(len(names) == len(index), 'Wiki名重複')
    require(len(pending['records']) == 181 and pending['imported_from_preservation_rows'] == 0,
            '受入済み181件の範囲が変わった')
    selected = []
    for source in pending['records']:
        key = source['species_key']
        require(key in manifests, '原本Species key欠落: ' + key)
        row = manifests[key]
        sid = int(row['id'])
        require(sid == source['species_id'] == int(row['vega_id']) == source['vega_id']
                and row['classification'] == 'VEGA_ORIGINAL' and row['is_official'] == 'false'
                and not row['form_key'] and int(row['canonical_national_dex']) == 0,
                'Species key/ID/domain衝突: ' + key)
        name = text(row['display_name'])
        require(name in names, 'Vega図鑑に名前がない: ' + name)
        selected.append(dict(names[name], species_id=sid, species_key=key, vega_id=sid,
                             manifest_display_name=row['display_name']))
    for key in ('species_id', 'species_key', 'dex_no', 'url'):
        require(len({r[key] for r in selected}) == 181, '181件joinの重複: ' + key)
    return sorted(selected, key=lambda r: r['species_id'])


class OriginalRom:
    """原作のpacked u16・egg headerを上限付きで読む。順序/重複は保持する。"""
    def __init__(self, raw):
        self.raw = raw

    def read(self, address, length):
        offset = address - ROM_BASE
        require(type(length) is int and length >= 0 and 0 <= offset <= len(self.raw) - length,
                '原作ROMの範囲外参照')
        return self.raw[offset:offset + length]

    def u16(self, address):
        return struct.unpack('<H', self.read(address, 2))[0]

    def pointer(self, site):
        address = struct.unpack('<I', self.read(ROM_BASE + site, 4))[0]
        require(address % 2 == 0, '非整列の原作table pointer')
        self.read(address, 1)
        return address

    def levels(self, address):
        result = []
        for order in range(256):
            offset = address - ROM_BASE + order * 2
            packed = self.u16(ROM_BASE + offset)
            if packed == 65535:
                return result
            move, level = packed & 511, packed >> 9
            require(0 < move < 512 and 0 <= level <= 100, '不正な原作level-up行')
            result.append({'move_id': move, 'level': level, 'order': order,
                           'source_offset': offset})
        raise SourceError('原作level-up終端がない')

    def eggs(self, address, species_count=412):
        result, active, seen = {}, None, set()
        for order in range(20000):
            offset = address - ROM_BASE + order * 2
            value = self.u16(ROM_BASE + offset)
            if value == 65535:
                return result
            if value >= 20000:
                active = value - 20000
                require(0 <= active < species_count and active not in seen,
                        '原作egg Species範囲/重複違反')
                seen.add(active)
                result[active] = []
            else:
                require(active is not None and 0 < value < 512, '不正な原作egg行')
                result[active].append({'move_id': value, 'order': len(result[active]),
                                       'source_offset': offset})
        raise SourceError('原作egg終端がない')


def original_from_archive(path, expected, rom_expected):
    require(path.is_file() and not path.is_symlink(), '原本assetが通常fileでない')
    require(path.stat().st_size == expected['size'], '原本asset size不一致')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    require(digest.hexdigest() == expected['sha256'], '原本asset SHA不一致')
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), '原本asset member重複')
        for info in archive.infolist():
            p = PurePosixPath(info.filename)
            require(not p.is_absolute() and '..' not in p.parts and '\\' not in info.filename
                    and not stat.S_ISLNK(info.external_attr >> 16), '原本assetの危険なmember')
        manifest = json.loads(archive.read('PRIVATE_ENVIRONMENT_MANIFEST.json'))
        require(manifest['schema_version'] == 1 and manifest['archive'] == path.name,
                '原本asset manifest不一致')
        rows = manifest['files']
        require(len({r['path'] for r in rows}) == len(rows)
                and set(names) == {r['path'] for r in rows} | {'PRIVATE_ENVIRONMENT_MANIFEST.json'},
                '原本assetの未宣言/重複member')
        selected = [r for r in rows if r['path'] == 'build/reference/vega.gba']
        require(len(selected) == 1, '凍結Vega ROM欠落')
        bound = selected[0]
        require(bound['size'] == rom_expected['rom_size']
                and bound['sha256'] == rom_expected['rom_sha256'], '凍結ROM identity衝突')
        require(archive.getinfo(bound['path']).file_size == bound['size'], '凍結ROM member size不一致')
        raw = archive.read(bound['path'])
        require(identity(raw) == {'size': bound['size'], 'sha256': bound['sha256']}, '凍結ROM byte不一致')
        return raw


def capture_rom(raw, roster, surface):
    rom = OriginalRom(raw)
    sites = {key: surface['pointer_sites'][key] for key in ('level_up', 'egg', 'tmhm', 'tutor', 'national_dex')}
    # 原作catalog rootの仮説を明示する。現代slot表へ暗黙に読み替えない。
    sites.update(machine_moves=0x1263D8, tutor_moves=0x1213D4)
    roots = {name: rom.pointer(site) for name, site in sites.items()}
    eggs = rom.eggs(roots['egg'])
    records = []
    for row in roster:
        sid = row['species_id']
        pointer = struct.unpack('<I', rom.read(roots['level_up'] + sid * 4, 4))[0]
        records.append(dict(row, level_up=rom.levels(pointer), egg=eggs.get(sid, []),
                            level_pointer=pointer))
    return {'rom': identity(raw), 'status': 'RAW_ORIGINAL_TABLES_NOT_RUNTIME_ACCEPTANCE',
            'records': records, 'pointer_sites': sites, 'roots': roots,
            'dex_values': list(struct.unpack('<411H', rom.read(roots['national_dex'], 822))),
            'compatibility_candidates': {
                family: {'bytes': list(rom.read(roots[family], 412 * 16)), 'strides_to_verify': [8, 16]}
                for family in ('tmhm', 'tutor')},
            'catalog_candidates': {
                family: list(struct.unpack('<128H', rom.read(roots[family], 256)))
                for family in ('machine_moves', 'tutor_moves')},
            'rom_changed': False, 'native_runs': 0, 'active_baseline_changed': False}
