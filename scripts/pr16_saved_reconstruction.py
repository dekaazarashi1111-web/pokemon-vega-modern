#!/usr/bin/env python3
"""保存済みbyteの正規化と再構成。旧run/build/compile/nativeは呼ばない。"""
from __future__ import annotations
import argparse
import ast
import io
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import urllib.request
import urllib.parse
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
import pr16_saved_recipe as s

REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
SELF = 'scripts/pr16_saved_reconstruction.py'
SEED = 'content/modernization/pr16_saved_reconstruction_seed.json'
NORMAL = 'content/modernization/pr16_saved_reconstruction_recipes.json'
OUT = ROOT/'.local/pr16-saved-reconstruction'
ANCHOR = 'build/stages/80_modernization_runtime_boundary_repair.gba'
BASE = 0x08000000
SIZE = 33554432
PARENT = dict(size=SIZE, sha256='6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3')
TARGET = dict(size=SIZE, sha256='2b107e7ef897844eff810ff0b40f82543640488696e8295194ceb3b66fb2c183')
PREVIOUS = 'content/modernization/pr16_circus_rental_resume.json'
_guard_active = False


def deny_process(event, args):
    if event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.fork', 'os.forkpty') or event.startswith('os.exec'):
        raise s.RecipeError('再構成中のprocess生成は禁止: '+event)


def process_barrier():
    global _guard_active
    if not _guard_active:
        sys.addaudithook(deny_process)
        _guard_active = True


def checked(path, expected):
    raw = s.safe(ROOT, path).read_bytes()
    s.need(s.identity(raw) == s.binding(expected), '保存入力identity不一致: '+path)
    return raw


def constants(name):
    """固定されたPythonのliteralのみ。module importやコード実行はしない。"""
    tree = ast.parse(s.safe(ROOT, name).read_text())
    result = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                result[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    return result


def u32(value):
    return struct.pack('<I', value)


def change(at, before, after):
    return dict(offset=at, before=before.hex(), after=after.hex())


def erased(at, data):
    return change(at, b'\xff'*len(data), data)


def canonical_identity(value):
    return s.binding({k: value[k] for k in ('size', 'sha256')})


def sparse_difference(left, right):
    """同じROMサイズのBPSを疎なbyteレシピへ変換。無変更範囲も確認する。"""
    s.need(type(left) is type(right) is bytes and len(left) == len(right), '固定サイズ差分が必要')
    edits = []
    for base in range(0, len(left), 4096):
        a, b = left[base:base+4096], right[base:base+4096]
        if a == b:
            continue
        index = 0
        while index < len(a):
            if a[index] == b[index]:
                index += 1
                continue
            start = index
            while index < len(a) and a[index] != b[index]:
                index += 1
            edits.append(change(base+start, a[start:index], b[start:index]))
    s.need(s.patch(left, edits) == right, '疎差分の全ROM照合に失敗')
    return edits


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        s.need(urllib.parse.urlsplit(newurl).scheme == 'https', '非HTTPSへのredirect禁止')
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if urllib.parse.urlsplit(req.full_url).netloc != urllib.parse.urlsplit(newurl).netloc:
            new.remove_header('Authorization')
        return new


class Originals:
    def __init__(self, seed, cache):
        self.seed, self.cache = seed, cache
        self.archives, self.used = {}, {}

    def read(self, label, member):
        model = self.seed['archives'][label]
        if label not in self.archives:
            if 'path' in model:
                raw = checked(model['path'], model['identity'])
            else:
                folder = self.cache/'originals'; folder.mkdir(parents=True, exist_ok=True)
                path = folder/(str(model['artifact_id'])+'.zip')
                if not path.exists():
                    token = os.environ.get('GH_TOKEN', '')
                    s.need(token, '固定artifact取得用tokenがない')
                    api = 'https://api.github.com/repos/'+REPO+'/actions/artifacts/'+str(model['artifact_id'])
                    headers = {'Authorization': 'Bearer '+token, 'Accept': 'application/vnd.github+json'}
                    def read_url(url):
                        with urllib.request.build_opener(SafeRedirect()).open(urllib.request.Request(url, headers=headers), timeout=120) as response:
                            return response.read()
                    meta = s.strict(read_url(api))
                    s.need(meta['workflow_run']['id'] == model['run_id'] and
                           meta['workflow_run']['head_sha'] == model['head_sha'] and
                           not meta['expired'] and meta['digest'] == 'sha256:'+model['identity']['sha256'],
                           '固定artifact metadata不一致: '+label)
                    raw = read_url(api+'/zip')
                    s.need(s.identity(raw) == model['identity'], '取得artifact identity不一致: '+label)
                    path.write_bytes(raw)
                raw = path.read_bytes()
                s.need(s.identity(raw) == model['identity'], 'cache artifact identity不一致: '+label)
            archive = zipfile.ZipFile(io.BytesIO(raw))
            names = archive.namelist()
            s.need(len(names) == len(set(names)), 'ZIP member重複')
            for name in names:
                p = Path(name)
                s.need(not p.is_absolute() and '..' not in p.parts and '\\' not in name, 'ZIP path不正')
            self.archives[label] = archive
        s.need(member in model['members'], '未固定member: '+member)
        raw = self.archives[label].read(member)
        s.need(s.identity(raw) == model['members'][member], '固定member identity不一致: '+member)
        self.used[label+'/'+member] = s.identity(raw)
        return raw

    def data(self, label, member):
        return s.strict(self.read(label, member))

    def code(self, label, member, address, expected):
        return s.disassembly_bytes(self.read(label, member).decode(), address, expected)


def make_entry(raw, report, originals):
    """保存済み受付graphとcode byte欄だけを再配置。旧run/compileは使わない。"""
    import pr16_circus_entry as old
    from tools.regression.rom_runtime import _charmap, _encode_text
    graph = originals.data('entry', 'pr16-circus-entry/parent-graphs.json')
    meta = originals.data('entry', 'pr16-circus-entry/facility-symbols.json')
    npc, nodes = graph['npc'], graph['nodes']
    for node in nodes + graph['gateway']:
        for instruction in node['instructions']:
            at, data = instruction['address']-BASE, bytes.fromhex(instruction['bytes'])
            s.need(0 <= at <= len(raw)-len(data) and raw[at:at+len(data)] == data, '保存graph preimage不一致')
    cancel = old.cancel_address(nodes, meta)
    entry_node = next(n for n in nodes if n['address'] == npc)
    rows = [r for r in entry_node['instructions'] if r['opcode'] == 15]
    s.need(len(rows) == 1, '保存prompt不明')
    old_prompt = struct.unpack_from('<I', bytes.fromhex(rows[0]['bytes']), 2)[0]
    offset, selector = report['payload_offset'], report['entries']['selector']
    code = originals.code('entry', 'pr16-circus-entry/compile-1/disassembly.txt', BASE+offset+64,
                          dict(size=276, sha256='f900831c70272390004e6d6584ffd8438c4e813c5298ec29b828b48473c6c69e'))
    thumb = 'scripts/pr16_circus_thumb.py'
    checked(thumb, report['sources'][thumb])
    adapter_size = constants(thumb)['ADAPTER_SIZE']
    s.need(adapter_size == 304 and len(code) == 276, '保存adapter境界不一致')
    # 固定原本compile_adapterの明示ljust規則。命令の欠損を推測で埋めない。
    code = code.ljust(adapter_size, b'\xff')
    payload = bytearray(64); payload[:8] = b'VEGAC18E'; payload.extend(code)
    while len(payload) % 4:
        payload.append(255)
    mapping, tokens = _charmap(ROOT)
    prompt = BASE+offset+len(payload)
    payload.extend(_encode_text('サーカスに さんかしますか？\nいいえで ファクトリーへ', mapping, tokens))
    trial_prompt = BASE+offset+len(payload)
    payload.extend(_encode_text('バトルサーカス トライアル！\nレンタルで 3れんせん しますか？', mapping, tokens))
    scripts, labels, sites, std = old.fork_graph(nodes, BASE+offset+len(payload), selector, old.DRAW, cancel, old_prompt, trial_prompt)
    payload.extend(scripts); bridge = BASE+offset+len(payload)
    payload.extend(old.bridge(bridge, prompt, labels[npc]))
    struct.pack_into('<8I', payload, 8, 1, len(payload), selector, labels[npc], bridge, 3, old.DRAW, 0)
    s.need(sites == report['launch_sites'] and std == report['rooted_std_edges'], '保存受付metadata不一致')
    s.need(s.identity(bytes(payload)) == report['payload'], '保存受付payload不一致')
    g = report['gateway']
    return [change(g['operand'], bytes.fromhex(g['before']), bytes.fromhex(g['after'])), erased(offset, bytes(payload))]


def normalize(output=OUT):
    process_barrier()
    seed = s.strict(s.safe(ROOT, SEED).read_bytes())
    for name, expected in seed['source_bindings'].items():
        checked(name, expected)
    output = output.absolute(); output.resolve().relative_to((ROOT/'.local').resolve())
    s.need(not any(p.is_symlink() for p in (output, *output.parents)), '出力symlink禁止')
    charmap = seed['charmap']; path = s.safe(ROOT, charmap['path'])
    lock = s.strict(s.safe(ROOT, 'state/source-lock.json').read_bytes())
    fixed = next(row for row in lock['sources'] if row['name'] == 'cfru')
    s.need(fixed['resolved_commit'] == charmap['commit'] and fixed['path']+'/charmap.tbl' == charmap['path'], '固定upstream不一致')
    if not path.exists():
        url = 'https://raw.githubusercontent.com/kapibarasan000/CFRU-JP/'+charmap['commit']+'/charmap.tbl'
        with urllib.request.urlopen(url, timeout=120) as response:
            data = response.read()
        s.need(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() == charmap['git_blob'], 'charmap blob不一致')
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
    data = path.read_bytes()
    s.need(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() == charmap['git_blob'], 'charmap blob不一致')
    originals = Originals(seed, output)
    anchor = raw = checked(ANCHOR, PARENT)
    recipes, provenance = [], []

    def append(name, report, patches):
        nonlocal raw
        recipe = dict(name=name, parent=canonical_identity(report['parent']),
                      candidate=canonical_identity(report['candidate']), patches=patches)
        if 'allocation' in report:
            recipe['allocation'] = report['allocation']
        raw, proof = s.apply_recipe(raw, recipe)
        recipes.append(recipe); provenance.append(dict(name=name, **proof))
        print(json.dumps(dict(layer=name, candidate=recipe['candidate'], patches=len(patches)), ensure_ascii=False), flush=True)

    def direct(name, target, patches):
        append(name, dict(parent=s.identity(raw), candidate=dict(size=SIZE, sha256=target)), patches)

    a = constants('tools/modernization_p03_native_pp_repair.py')
    direct('Stage81保存PP literal', a['CANDIDATE_SHA'], [change(row[0], u32(a['OLD_PP']), u32(a['CANONICAL_MOVES']+4)) for row in a['SITES']])
    a = constants('tools/modernization_p03_archive_ui_repair.py')
    direct('Stage82保存UI byte', a['CANDIDATE_SHA'], [change(at, bytes.fromhex(before), bytes.fromhex(after)) for _, at, before, after in a['SITES']])
    a = seed['stage83']
    append('Stage83保存採用3項目', a, [change(r['offset'], bytes.fromhex(r['before_hex']), bytes.fromhex(r['after_hex'])) for r in a['changes']])
    direct('Stage84保存empty PP', '55cf145e7dd1c8e2568fe9c733b597f8c4bc3d31b7d6fa233a7b4821d1b62c3b', [change(0x10421f8, b'\x23', b'\0')])
    from tools.release.bps import apply_bps
    for label, forward, reverse, report in seed['bps_layers']:
        candidate = originals.data(label, report)
        new = apply_bps(raw, originals.read(label, forward))
        s.need(apply_bps(new, originals.read(label, reverse)) == raw, '保存逆BPSの全ROM不一致')
        append(label+'保存BPS', candidate, sparse_difference(raw, new))
    direct('Trial保存pointer', 'df8a15c3b464854ca84a5c0533177cfa3187b5eef252d20248f7654edb72887c', [change(0x13c93c1, bytes.fromhex('90f72c09'), bytes.fromhex('a4d43809'))])
    direct('Chooser保存U16', 'bffd0b83e3724c2fba216052a3ff45afd3ab194ca2168244874746ce0e4a9e92', [change(0x12cf629, bytes.fromhex('2f00'), bytes.fromhex('2900'))])
    a = originals.data('bp-loss', 'pr16-bp-loss-return-run/successor-candidate.json')
    code = originals.code('bp-loss', 'pr16-bp-loss-return-run/successor-compile-1-runtime-disassembly.txt', BASE+a['payload']['offset'], a['runtime'])
    append('BP保存敗北復帰', a, [a['change'], erased(a['payload']['offset'], code)])
    a = s.strict(s.safe(ROOT, 'content/modernization/pr16_bp_exchange_abi_verified.json').read_bytes())
    append('BP保存exchange ABI', a, a['changes'])
    a = originals.data('bp-retention', 'pr16-bp-party-retention-native-run/successor-candidate.json')
    append('BP保存party保持', a, a['changes'])
    a = originals.data('gift', 'pr16-ring-npc-successor/candidate.json')
    import pr16_ring_npc_successor as gift
    code = originals.code('gift', 'pr16-ring-npc-successor/compile-1/disassembly.txt', BASE+a['payload_offset']+64,
                          dict(size=128, sha256='5dca1ccb61c5fe0e86fdc8c2d7e7f581a71aa5fdaf7d0bceddb6cc001ea56651'))
    template = gift.map_view(raw, gift.TEMPLATE_MAP)
    template = template['raw_objects'][template['ids'].index(2)*24:][:24]
    xy = a['map']['npc']['x'], a['map']['npc']['y']
    payload, details = gift.make_payload(raw, a['payload_offset'], code, a['map']['native_entry'], xy, template)
    s.need(s.identity(payload) == a['payload'] and details == a['map'], '保存gift byte不一致')
    append('Ring保存gift', a, [change(details['header']+4-BASE, u32(details['old_events']), u32(details['new_events'])), erased(a['payload_offset'], payload)])
    a = originals.data('policy', 'pr16-ring-policy-successor/candidate.json')
    code = originals.code('policy', 'pr16-ring-policy-successor/compile-1/disassembly.txt', a['entry']&~1,
                          dict(size=124, sha256='933c62609ab0b40da2851183e10296b1c938767d69dcf3cbbe646d7eb81721ed'))
    prologue = bytes.fromhex(a['displaced_prologue_hex'])
    jump = lambda pointer: bytes.fromhex('004b1847')+u32(pointer)
    payload = struct.pack('<8sIIIIII', b'VEGAR18P', 1, 48+len(code), a['original_begin'], a['trampoline'], a['entry'], 0)+prologue+jump(a['original_resume'])+code
    s.need(s.identity(payload) == a['payload'], '保存policy payload不一致')
    append('Ring保存通常policy', a, [change(a['original_begin']-BASE, prologue, jump(a['entry'])), erased(a['payload_offset'], payload)])
    a = originals.data('entry', 'pr16-circus-entry/report.json')
    append('Circus保存実受付', a, make_entry(raw, a, originals))
    a = originals.data('retention', 'pr16-circus-retention-build/report.json'); p = a['proof']
    code = originals.code('retention', 'pr16-circus-retention-build/compile-1/disassembly.txt', BASE+p['payload_offset'], p['payload'])
    append('Circus保存個体保持', a, [change(p['literal_offset'], u32(p['previous_entry']), u32(p['new_entry'])), erased(p['payload_offset'], code)])
    a = s.strict(s.safe(ROOT, 'content/modernization/pr16_circus_three_win.json').read_bytes())['native']['build_recipe']
    append('Circus保存連続戦', a, a['patches'])
    a = s.strict(s.safe(ROOT, 'content/modernization/pr16_circus_coldboot.json').read_bytes())['build']
    append('Circus保存coldboot', a, a['patches'])
    latest = s.strict(s.safe(ROOT, PREVIOUS).read_bytes())['build']
    for name, a in [('Circus保存drought親', latest['old']), ('Circus保存rental drought', latest)]:
        append(name, a, a['patches'])
    # 同じmanifestだけで前進/全鎖逆適用。旧adapterや再構成generatorへのfallbackなし。
    rebuilt, proof = s.chain(anchor, recipes, TARGET)
    s.need(rebuilt == raw and _guard_active, '保存全鎖またはprocess barrier不一致')
    normal = dict(schema_version=1, anchor=dict(path=ANCHOR, **PARENT), candidate=TARGET, recipes=recipes,
                  provenance=dict(seed=s.identity(s.safe(ROOT, SEED).read_bytes()), original_members=originals.used),
                  runtime_metadata=latest, native_acceptance=False, release_ready=False)
    output.mkdir(parents=True, exist_ok=True)
    (output/'normalized-recipes.json').write_bytes(s.stable(normal))
    report = dict(schema_version=1, classification='SAVED_BYTE_CHAIN_VERIFIED_NO_RECOMPILE',
                  tested_head=os.environ.get('GITHUB_SHA'), run_id=int(os.environ.get('GITHUB_RUN_ID','0')),
                  candidate=TARGET, reconstruction=proof, process_barrier_active=True,
                  process_spawns=0, arm_compiles=0, arm_links=0, new_emulator_processes=0,
                  accepted_native_cases_replayed=0, accepted_host_tests_replayed=0,
                  normalized_recipe=s.identity(s.stable(normal)), seed=s.identity(s.safe(ROOT, SEED).read_bytes()),
                  source_bindings={p:s.identity(s.safe(ROOT,p).read_bytes()) for p in (SELF,SEED,'scripts/pr16_saved_recipe.py')},
                  original_members=originals.used, rom_changes=0, physical_admission_accepted=False,
                  genuine_30_wins_verified=False, suppression_accepted=False, release_ready=False)
    (output/'reconstruction.json').write_bytes(s.stable(report))
    s.need(checked(ANCHOR,PARENT) == anchor, '固定親が変更された')
    return report


def reconstruct(output):
    """通常再開は固定JSONと核のみ。normalize、旧builder、networkを一切使わない。"""
    process_barrier()
    model = s.strict(s.safe(ROOT, NORMAL).read_bytes())
    s.need(model['anchor'] == dict(path=ANCHOR, **PARENT) and model['candidate'] == TARGET, '保存正本identity不一致')
    raw = checked(ANCHOR, PARENT)
    new, proof = s.chain(raw, model['recipes'], TARGET)
    output = output.absolute(); output.resolve().relative_to((ROOT/'.local').resolve())
    s.need(not any(p.is_symlink() for p in (output, *output.parents)), '出力symlink禁止')
    output.mkdir(parents=True, exist_ok=True)
    (output/'candidate.gba').write_bytes(new)
    (output/'report.json').write_bytes(s.stable(model['runtime_metadata']))
    (output/'reconstruction.json').write_bytes(s.stable(proof))
    s.need(checked(ANCHOR, PARENT) == raw, '固定親が変更された')
    return proof


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('normalize', 'reconstruct'))
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    try:
        result = normalize(args.output) if args.command == 'normalize' else reconstruct(args.output)
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile) as error:
        print(type(error).__name__+': '+str(error), file=sys.stderr)
        raise SystemExit(1)
