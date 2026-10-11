#!/usr/bin/env python3
"""固定R0を改作せず、人向け表示と自己完結Markdownパッケージを作る。"""
from __future__ import annotations
import argparse
import hashlib
import html
import io
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import tempfile
from urllib.parse import unquote, urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = 'docs/wiki/r0-6e88a021'
OUT = 'docs/wiki/r0.1-6e88a021'
BASE_COMMIT = '473aca371dbfd1d8a041d2ead4326a54759dcda4'
BASE_INDEX_SHA = '7e759871deaae756baebc84f5eee5ad78350209d24f28c1a8d6db1c1d60e773b'
HINT = '## 現役の直接データからの検索補助\n'
SUPPLY = '## 入手・解禁・隠れ特性の境界\n'
LEARN = '## 現役の全習得・元順序・供給条件\n'
INVERSE = '## 全経路の逆引き（後継原本表示）\n'
STATS = ('hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed', 'total')
LINK = re.compile(r'(?<!!)\[[^\]\n]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)')
ANCHOR = re.compile(r'<a\s+id="([^"]+)"\s*>')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def compact(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def identity(raw):
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}


def path_ok(name):
    p = PurePosixPath(name)
    need(name == p.as_posix() and not p.is_absolute() and '..' not in p.parts and '\\' not in name, '危険な相対path')
    need(p.suffix in {'.md', '.json', '.jsonl'}, '資料以外のmember')
    return p


def read(root, name):
    p = root
    for part in PurePosixPath(name).parts:
        p /= part
        need(not p.is_symlink(), 'symlink禁止')
    return p.read_bytes()


def records(raw):
    return [json.loads(line) for line in raw.splitlines()]


def esc(value):
    return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('|', '&#124;').replace('\n', '<br>').replace('[', '&#91;').replace(']', '&#93;')


def table(headers, rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(str, row))+' |\n' for row in rows)+'\n'


def link(kind, row):
    return '['+esc(row['name'])+']('+kind+'/'+str(row['id'])+'.md)'


def heading(title):
    return '# '+title+'\n\n**R0.1（閲覧改善版）** — 固定R0と同じゲーム情報。ゲーム投入用ではありません。\n\n[入口](README.md) · [制限](LIMITATIONS.md) · [識別情報](data/index.json)\n\n'


def collapse_json(text):
    return re.sub(r'```json\n.*?\n```', lambda m: '<details>\n<summary>技術詳細・原本JSON（確認範囲を含む）</summary>\n\n'+m[0]+'\n\n</details>', text, flags=re.S)


def project_detail(name, raw):
    text = raw.decode()
    if name.startswith('pokemon/'):
        need(text.count(HINT) == text.count(SUPPLY) == text.count(LEARN) == 1, '種族表示の境界変更')
        before, rest = text.split(HINT, 1)
        _, after = rest.split(SUPPLY, 1)
        text = before+'## 習得の確認\n\n役割は未分類・要全習得確認です。非網羅な候補と空抽出を「覚えない」根拠にしないため、役割要約を掲載しません。[このページの全習得表](#all-learning)で直接習得・持越し・条件付き繁殖・供給条件を区別してください。\n\n'+SUPPLY+after
        prefix, body = text.split(LEARN, 1)
        text = collapse_json(prefix)+'<a id="all-learning"></a>\n\n'+LEARN+body
    elif name.startswith('moves/'):
        need(text.count(INVERSE) == 1, '技逆引き境界変更')
        prefix, body = text.split(INVERSE, 1)
        text = collapse_json(prefix)+INVERSE+body
    elif name.startswith(('abilities/', 'items/', 'mega/', 'gmax/', 'z/')):
        text = collapse_json(text)
    return text.replace('**固定レビュー版 R0**', '**R0.1（閲覧改善版）**', 1).encode()


def special_value(value, field):
    if field == 'accuracy' and value == 0:
        return '特殊（原本0・0%とは断定しない）'
    if field == 'power' and value in (0, 1):
        return '特殊/変化（原本'+str(value)+'・詳細確認）'
    if field == 'pp' and value == 0:
        return '0（使用可否は詳細確認）'
    return str(value)


def game_projection(files):
    sp = records(files['data/species.jsonl'])
    for s in sp:
        s.pop('role_search_hints', None)
    return {'species': sp, **{n: identity(files[n]) for n in ('data/moves.jsonl', 'data/abilities.jsonl', 'data/mechanics.json', 'data/active_sources.json')}}


def validate_links(files):
    anchors = {n: set(ANCHOR.findall(raw.decode())) for n, raw in files.items() if n.endswith('.md')}
    count = 0
    for name, raw in files.items():
        if not name.endswith('.md'):
            continue
        text = re.sub(r'```.*?```', '', raw.decode(), flags=re.S)
        for target in LINK.findall(text):
            u = urlsplit(html.unescape(target))
            need(not u.scheme and not u.netloc and not u.query, '外部Markdownリンク')
            path = unquote(u.path)
            need(not path.startswith('/') and '\\' not in path, '絶対リンク')
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), path)) if path else name
            need(resolved in files, 'リンク先欠落: '+name+' -> '+target)
            if u.fragment:
                need(unquote(u.fragment) in anchors.get(resolved, set()), 'anchor欠落: '+target)
            count += 1
    return count


def load_base(root):
    raw = read(root, BASE+'/data/index.json')
    need(identity(raw)['sha256'] == BASE_INDEX_SHA, '固定R0 manifest不一致')
    index = json.loads(raw)
    expected = set(index['files']) | {'data/index.json'}
    folder = root/BASE
    need({p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()} == expected, 'R0集合不一致')
    files = {}
    for name, binding in index['files'].items():
        path_ok(name)
        files[name] = read(root, BASE+'/'+name)
        need(identity(files[name]) == binding, 'R0 byte不一致: '+name)
    return files, index, raw


def render(base, index, index_raw, source_head):
    need(bool(re.fullmatch('[0-9a-f]{40}', source_head)), 'source HEAD不正')
    files = {n: project_detail(n, raw) if n.endswith('.md') else raw for n, raw in base.items()}
    species = records(base['data/species.jsonl'])
    moves = records(base['data/moves.jsonl'])
    abilities = records(base['data/abilities.jsonl'])
    need([s['id'] for s in species] == list(range(1671)), '種族集合')
    need([m['id'] for m in moves] == list(range(1063)), '技集合')
    need([a['id'] for a in abilities] == list(range(318)), '特性集合')
    vega = [int(x) for x in re.findall(r'^\| \[\d+: [^\n]+?\]\(pokemon/(\d+)\.md\)', base['VEGA_BALANCE_INDEX.md'].decode(), re.M)]
    need(len(vega) == len(set(vega)) == 206, 'ベガ対象集合')
    metadata = {}
    for s in species:
        text = base['pokemon/'+str(s['id'])+'.md'].decode()
        m = re.search(r'^分類: (.*?) / 全国番号: (\d+) /', text, re.M)
        need(m is not None, '分類表示欠落')
        metadata[s['id']] = {'classification': m[1], 'national_no': int(m[2])}
    def comparison(ids):
        rows = []
        for sid in ids:
            s = species[sid]
            form = s['form_key'].removeprefix('FORM_KEY_') or '通常（フォームキーなし）'
            if sid == 0 or 'INTERNAL' in metadata[sid]['classification'] or 'UNUSED' in metadata[sid]['classification']:
                form = '内部用/予約行 · '+form
            rows.append([link('pokemon', s), esc(form), esc('/'.join(dict.fromkeys(s['type_names']))), *[s['base_stats'][k] for k in STATS], *[link('abilities', abilities[a]) if a else '未割当（0）' for a in s['ability_ids']], str(sid)])
        return table(['名前・全習得', 'フォーム/区分', 'タイプ', 'HP', '攻撃', '防御', '特攻', '特防', '素早さ', '合計', '通常特性1', '通常特性2', '夢特性', 'ID'], rows)
    files['VEGA_BALANCE_INDEX.md'] = (heading('ベガと関連フォーム206行の比較')+'対象集合はR0と同じです。役割候補の件数は掲載しません。名前から個別の全習得表へ移れます。\n\n'+comparison(vega)).encode()
    files['POKEMON_INDEX.md'] = (heading('全1671種族・フォーム')+'[ベガのみの比較](VEGA_BALANCE_INDEX.md)。内部用/予約行も識別用に含み、収集数や自然入手可能数ではありません。分類の原本値は個別ページと参考JSONに保持します。\n\n'+comparison(range(1671))).encode()
    descriptions = {}
    for m in moves:
        text = base['moves/'+str(m['id'])+'.md'].decode()
        match = re.search(r'^説明: (.*?)。0威力/命中等の特殊解釈', text, re.M)
        need(match is not None, '技説明欠落')
        descriptions[m['id']] = match[1]
    files['MOVE_INDEX.md'] = (heading('全1063技の性能と説明')+'説明は既存文字列で、完全な実効果仕様ではありません。特殊値は通常の威力や命中率と断定せず、詳細の効果定義・確認範囲を参照してください。\n\n'+table(['技・詳細', 'タイプ', '分類', '威力', '命中', 'PP', '優先度', '既存の説明', 'ID'], [[link('moves', m), esc(m['type_name']), esc(m['category']), *[special_value(m[k], k) for k in ('power', 'accuracy', 'pp')], m['priority'], descriptions[m['id']], m['id']] for m in moves])).encode()
    files['ABILITY_INDEX.md'] = (heading('全318特性の説明と所持対象')+'特性名からslot別の全所持対象へ移れます。長いhandler/native辞書は詳細の折り畳みに保持。未確認を未実装・使用不能とは扱いません。\n\n'+table(['特性・所持対象', '既存の説明', '所持slot数', '確認状態', 'ID'], [[link('abilities', a), esc(a['description']), len(a['owners']), '個別の証拠範囲を参照', a['id']] for a in abilities])).encode()
    legacy = []
    for s in species:
        legacy.append({'species_id': s['id'], 'status': 'LEGACY_INCOMPLETE_NOT_FOR_DECISIONS', 'role_search_hints': s.pop('role_search_hints')})
    files['data/species.jsonl'] = b''.join(compact(s) for s in species)
    files['data/legacy_role_hints.jsonl'] = b''.join(compact(s) for s in legacy)
    files['data/classification.json'] = encode(metadata)
    files['data/r0_input_manifest.json'] = index_raw
    files['README.md'] = (heading('ポケモンベガ Modern 閲覧資料')+'''まず[ベガ比較](VEGA_BALANCE_INDEX.md)を開き、必要な場合だけ[全種族](POKEMON_INDEX.md)へ進みます。気になる名前から個別ページの「全習得」を読み、関連する[技](MOVE_INDEX.md)・[特性](ABILITY_INDEX.md)の詳細へ移ってください。4,514ページを一括でAIへ渡す必要はありません。

基本性能・全習得経路/条件・機構対応は固定R0から不変です。役割要約の取りこぼしを判断根拠から外し、表示だけを改善しました。バランス変更案や実装承認は含みません。

[道具](ITEM_INDEX.md) · [メガ](MEGA_INDEX.md) · [Gmax](GMAX_INDEX.md) · [専用Z](Z_MOVE_INDEX.md) · [供給条件](SUPPLY_CONDITIONS.md) · [隠れ特性](HIDDEN_ABILITY_INDEX.md) · [旧基準との差分](DIFF_INDEX.md)

## ローカル保存と別AIへの渡し方

閲覧用ZIP `wiki-r0.1-6e88a021.zip` を展開し、`r0.1-6e88a021/README.md` をMarkdown対応エディタで開きます。主要一覧と全詳細を同梱し、Markdownの相対リンクは展開後も内部で完結します。ZIPと全memberのsize/SHA-256は同時提供の検証記録にあります。

リポジトリからの再現は `python3 -B scripts/pr16_wiki_readability.py package --output .local/wiki-r0.1-6e88a021.zip`。完成済み閲覧版のhashを照合して資料だけをZIP化します。ROM/save/private入力/.git/実行環境は含みません。公開Releaseは作りません。

別AIには「この固定版のベガ比較→指定した系統の全習得→関連する技/特性詳細だけを読み、検討に使ってください。原本やゲームは編集せず、習得・自然供給・効果の未確認を区別してください」と伝えます。

[参考JSONの読み方](CODEX_INDEX.md)は必要時だけ参照。これはゲームへ直接投入するデータではありません。保存安全性・配布受入の完了宣言でもありません。
''').encode()
    files['CODEX_INDEX.md'] = (heading('参考JSONと固定入力')+'''[版/全member manifest](data/index.json)、[種族](data/species.jsonl)、[技](data/moves.jsonl)、[特性](data/abilities.jsonl)、[機構](data/mechanics.json)、[分類の原本値](data/classification.json)を提供します。ID/stable key/原本証拠は削除せず、主要MDから分離しました。

非網羅な旧役割抽出は [履歴専用JSON](data/legacy_role_hints.jsonl) へ隔離しています。空抽出は技の不存在を意味せず、判断用タグとして使用しないでください。

[固定R0入力manifest](data/r0_input_manifest.json) と [現役原本参照](data/active_sources.json) 内のrepository pathは由来の記録です。旧候補/Issue19の全機械読取原本や実行コードはこのZIPに含みません。それらが必要な監査は固定リポジトリを参照してください。通常閲覧用の全習得・条件・逆引きMarkdownは同梱済みで、そのリンクに外部依存はありません。

`check` は再生成byte・集合・リンク・mtimeを照合する読取専用コマンドです。`package` は既存版を検査し明示したZIPだけを書きます。ゲーム情報の意味hashと表示用tree hashを別々に記録します。
''').encode()
    files['LIMITATIONS.md'] = (heading('閲覧版の制限')+'''R0.1は固定R0と同一候補の閲覧資料です。説明文字列は完全な実効果仕様ではありません。役割要約は非網羅のため主要表・個別ページから除外し、未分類は全習得表で確認します。

以下はR0時点の証拠境界の引用です。容量784/90等は歴史値であり現在の技術frontierではありません。閲覧改善開始時の現在台帳は788分類/86未知・選定残7・安全容量0。どちらも保存統合完了を示しません。

---

'''+base['LIMITATIONS.md'].decode()).encode()
    need(game_projection(base) == game_projection(files), 'ゲーム情報の意味差分')
    for name, raw in base.items():
        if name.startswith('pokemon/'):
            need(raw.split(LEARN.encode(), 1)[1] == files[name].split(LEARN.encode(), 1)[1], '全習得byte差分')
            need(HINT.encode() not in files[name] and b'**\xe5\x9b\x9e\xe5\xbe\xa9\xe5\x80\x99\xe8\xa3\x9c**' not in files[name], '役割要約の残存')
        if name.startswith('moves/'):
            need(raw.split(INVERSE.encode(), 1)[1] == files[name].split(INVERSE.encode(), 1)[1], '逆引きbyte差分')
        if name.startswith('conditions/'):
            need(raw == files[name], '条件byte差分')
    known = files['pokemon/3.md'].decode().split(LEARN, 1)[1]
    need(any('こうごうせい' in line and re.search(r'\b46\b', line) for line in known.splitlines()), 'リーテイルLv46こうごうせい欠落')
    manifest = {'schema_version': 1, 'revision': 'R0.1', 'source_head': source_head, 'base_commit': BASE_COMMIT, 'base_manifest': identity(index_raw), 'candidate': index['candidate'], 'core_game_semantic_sha256': identity(compact(game_projection(files)))['sha256'], 'core_game_semantics_unchanged': True, 'role_hints_policy': 'REMOVED_FROM_REVIEW_ISOLATED_LEGACY', 'counts': index['counts'], 'files': {n: identity(raw) for n, raw in sorted(files.items())}}
    manifest['tree_sha256'] = identity(compact(manifest['files']))['sha256']
    files['data/index.json'] = encode(manifest)
    return files, manifest


def generate(root, source_head):
    return render(*load_base(root), source_head)


def write_files(root, files):
    folder = root/OUT
    if folder.exists():
        need({p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()} <= set(files), 'stale出力は削除しない')
    for name, raw in files.items():
        path_ok(name)
        path = root
        for part in PurePosixPath(OUT+'/'+name).parts:
            path /= part
            need(not path.is_symlink(), '出力symlink禁止')
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_bytes() != raw:
            path.write_bytes(raw)


def read_output(root):
    manifest = json.loads(read(root, OUT+'/data/index.json'))
    need(manifest['revision'] == 'R0.1' and manifest['base_manifest']['sha256'] == BASE_INDEX_SHA, '閲覧版identity')
    need(identity(compact(manifest['files']))['sha256'] == manifest['tree_sha256'], 'manifest tree hash')
    expected = set(manifest['files']) | {'data/index.json'}
    folder = root/OUT
    need({p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()} == expected, '閲覧版集合')
    files = {}
    for name in expected:
        path_ok(name)
        files[name] = read(root, OUT+'/'+name)
        if name != 'data/index.json':
            need(identity(files[name]) == manifest['files'][name], '閲覧版member hash: '+name)
    validate_links(files)
    return files, manifest


def check(root):
    names = [p for folder in (root/BASE, root/OUT) for p in folder.rglob('*') if p.is_file()]
    before = {str(p): (p.stat().st_mtime_ns, identity(p.read_bytes())) for p in names}
    actual, manifest = read_output(root)
    expected, _ = generate(root, manifest['source_head'])
    need(actual == expected, '決定的生成不一致')
    need(before == {str(p): (p.stat().st_mtime_ns, identity(p.read_bytes())) for p in names}, 'check副作用')
    return {'status': 'PASS', 'files': len(actual), 'bytes': sum(map(len, actual.values())), 'links': validate_links(actual), 'deterministic': True, 'read_only_byte_mtime': True, 'core_game_semantics_unchanged': True, 'known_regression': '役割要約を全種から除外、リーテイルLv46こうごうせいと全習得byte不変', 'tree_sha256': manifest['tree_sha256'], 'core_game_semantic_sha256': manifest['core_game_semantic_sha256']}


def package(root, output):
    files, manifest = read_output(root)
    output = Path(output).resolve()
    need(not output.is_relative_to((root/OUT).resolve()) and not output.is_relative_to((root/BASE).resolve()), '固定資料内へのZIP書込禁止')
    def archive_bytes():
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for name, raw in sorted(files.items()):
                path_ok(name)
                zi = zipfile.ZipInfo('r0.1-6e88a021/'+name, (1980, 1, 1, 0, 0, 0))
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.external_attr = 0o100644 << 16
                z.writestr(zi, raw, compresslevel=9)
        return buf.getvalue()
    raw = archive_bytes()
    need(raw == archive_bytes(), 'ZIP決定性不一致')
    with zipfile.ZipFile(io.BytesIO(raw)) as z, tempfile.TemporaryDirectory() as td:
        expected = {'r0.1-6e88a021/'+n for n in files}
        need(set(z.namelist()) == expected and len(z.namelist()) == len(expected), 'ZIP集合/重複')
        for info in z.infolist():
            need((info.external_attr >> 16) == 0o100644, 'ZIP非通常file')
            need(identity(z.read(info)) == identity(files[info.filename.split('/', 1)[1]]), 'ZIP member hash')
        z.extractall(td)
        expanded = {n: (Path(td)/'r0.1-6e88a021'/n).read_bytes() for n in files}
        need(expanded == files and (Path(td)/'r0.1-6e88a021/README.md').is_file(), '展開byte/入口')
        links = validate_links(expanded)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    return {'name': output.name, **identity(raw), 'files': len(files), 'uncompressed_bytes': sum(map(len, files.values())), 'expanded_links': links, 'expanded_verified': True, 'deterministic': True, 'private_inputs_included': False, 'manifest_sha256': identity(files['data/index.json'])['sha256'], 'tree_sha256': manifest['tree_sha256']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('build', 'check', 'package'))
    p.add_argument('--source-head')
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    if args.command == 'build':
        files, _ = generate(ROOT, args.source_head or '')
        validate_links(files)
        write_files(ROOT, files)
        result = check(ROOT)
    elif args.command == 'check':
        result = check(ROOT)
    else:
        need(args.output is not None, '--outputが必要')
        result = package(ROOT, args.output)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
