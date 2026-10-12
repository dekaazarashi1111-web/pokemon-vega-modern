#!/usr/bin/env python3
"""P08候補の保存byte連鎖・正味差分・共有owner影響。native受入と混同しない。"""
from __future__ import annotations
import hashlib
from pathlib import Path
import sys
import zlib
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_saved_recipe as saved

ROOT = Path(__file__).resolve().parents[1]
SELF = 'scripts/pr16_p08_impact.py'
NORMAL = 'content/modernization/pr16_saved_reconstruction_recipes.json'
GETTER = 'content/modernization/pr16_circus_getter_followup.json'
CIRCUS = 'content/modernization/pr16_circus_acceptance.json'
INPUTS = {
    NORMAL: dict(size=1249360, sha256='80d93a1de6175eaffb391baf1d38a0de8ec647c90b837863e2703868e33d1bd5'),
    GETTER: dict(size=117299, sha256='856881aa9b0156f391736de4748733395f493fe3de48ac23596e828c5745ba27'),
}
TARGET = dict(size=33554432, sha256='46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38')
PREFIX = dict(size=33554432, sha256='2b107e7ef897844eff810ff0b40f82543640488696e8295194ceb3b66fb2c183')
ANCHOR = dict(size=33554432, sha256='6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3')
ANCHOR_PATH = 'build/stages/80_modernization_runtime_boundary_repair.gba'
REPORTS = {
    'P03_P06_P07': 'content/modernization/pr16_completion_acceptance.json',
    'GENERIC_FORM': 'content/modernization/pr16_generic_form_acceptance.json',
    'FIXED_FORM': 'content/modernization/pr16_fixed_form_acceptance.json',
    'BP': 'content/modernization/pr16_bp_chooser_checkpoint.json',
    'RING': 'content/modernization/pr16_ring_policy_acceptance.json',
    'CIRCUS': CIRCUS,
}
# 既存コードが書き換える共有entry。サイズは保存patchそのものと照合する。
HOOKS = (
    (0x5ec, 4, 'SAVE_DISPATCH'), (0xdb4e8, 4, 'LOAD_DISPATCH'),
    (0x7fc5c, 4, 'BATTLE_LOSS_RETURN'), (0x389a0c, 4, 'DROUGHT_BATTLE_CALLBACK'),
    (0x10dd51c, 4, 'PARTY_RESTORE_CALL'), (0x1103380, 4, 'FACTORY_GETTER_CALL'),
    (0x11266f4, 8, 'RING_ORDINARY_BEGIN'),
)
need = saved.need


def checked(root, path, expected):
    raw = saved.safe(root, path).read_bytes()
    need(saved.identity(raw) == expected, 'source identity differs: ' + path)
    return saved.strict(raw)


def chain_model(normal, getter):
    need(normal['schema_version'] == 1 and normal['anchor'] == dict(path=ANCHOR_PATH, **ANCHOR), 'anchor binding')
    need(normal['candidate'] == PREFIX and len(normal['recipes']) == 20, 'saved prefix binding')
    tail = getter['build']
    need(tail['parent'] == PREFIX and tail['candidate'] == TARGET and len(tail['patches']) == 7, 'saved successor binding')
    recipes = [*normal['recipes'], dict(name='Circus保存getter ABI/typed-field',
        parent=tail['parent'], candidate=tail['candidate'], patches=tail['patches'], allocation=tail['allocation'])]
    previous, seen = ANCHOR, {ANCHOR['sha256']}
    for recipe in recipes:
        need(saved.binding(recipe['parent']) == previous, 'broken candidate ancestry')
        previous = saved.binding(recipe['candidate'])
        need(previous['size'] == TARGET['size'] and previous['sha256'] not in seen, 'cyclic/variable-size ancestry')
        seen.add(previous['sha256'])
    need(previous == TARGET, 'terminal candidate binding')
    # 疎な重複preimage照合をROM入手前にも実施する。
    sparse(recipes)
    return recipes


def sparse(recipes):
    """親→最終の正味差分。取消済みbyteを除去し、重なる後続patchのpreimageを照合。"""
    first, last = {}, {}
    for recipe in recipes:
        cursor = 0
        need(type(recipe['patches']) is list and recipe['patches'], 'empty layer')
        for row in sorted(recipe['patches'], key=lambda r: r['offset']):
            at = row['offset']; before = saved.hex_bytes(row['before']); after = saved.hex_bytes(row['after'])
            need(type(at) is int and cursor <= at <= TARGET['size']-len(before), 'overlapping/outside patch')
            need(len(before) == len(after) and before != after, 'fixed-size change required')
            for offset, old, new in zip(range(at, at+len(before)), before, after):
                need(offset not in last or last[offset] == old, 'cross-layer preimage differs')
                first.setdefault(offset, old); last[offset] = new
            cursor = at+len(before)
    keys = sorted(k for k in first if first[k] != last[k])
    result = []
    for k in keys:
        if not result or result[-1]['end_exclusive'] != k:
            result.append(dict(start=k, end_exclusive=k, before=bytearray(), after=bytearray()))
        row = result[-1]; row['end_exclusive'] += 1; row['before'].append(first[k]); row['after'].append(last[k])
    return [dict(start=r['start'], end_exclusive=r['end_exclusive'], size=r['end_exclusive']-r['start'],
                 before=bytes(r['before']).hex(), after=bytes(r['after']).hex()) for r in result]


def intersects(start, end, row):
    return start < row['end_exclusive'] and row['start'] < end


def labels(start, end, allocations):
    owners = [r['name'] for r in allocations if intersects(start, end, r)]
    owners += [name for at, size, name in HOOKS if start < at+size and at < end]
    if not owners:
        owners = ['BASE_ROM_OR_RESERVED_OWNER_REQUIRES_REVIEW']
    return sorted(owners)


def describe(rows, allocations):
    return [dict(start=r['start'], end_exclusive=r['end_exclusive'], size=r['size'],
                 before_sha256=hashlib.sha256(bytes.fromhex(r['before'])).hexdigest(),
                 after_sha256=hashlib.sha256(bytes.fromhex(r['after'])).hexdigest(),
                 owners=labels(r['start'], r['end_exclusive'], allocations)) for r in rows]


def impact(recipes, candidate, allocations):
    positions = [i for i, r in enumerate(recipes) if r['candidate'] == candidate]
    need(len(positions) == 1, 'accepted candidate not in exact ancestry')
    rest = recipes[positions[0]+1:]
    changes = sparse(rest)
    owners = sorted({owner for r in changes for owner in labels(r['start'], r['end_exclusive'], allocations)})
    hooks = [name for at, size, name in HOOKS if any(intersects(at, at+size, r) for r in changes)]
    return dict(parent=candidate, candidate=TARGET, later_layers=len(rest),
                changed_bytes=sum(r['size'] for r in changes), changed_ranges=describe(changes, allocations),
                affected_owners=owners, shared_hooks=hooks,
                exact_candidate=(candidate == TARGET), native_transfer_accepted=(candidate == TARGET),
                unaffected_native_cases_replayed=0,
                decision='SAME_CANDIDATE_INHERIT' if candidate == TARGET else 'SHARED_RUNTIME_REVIEW_REQUIRED')


def source_review(root, value):
    """旧原本のsource bindingを改作せず、現状との一致/不一致を別receiptに記録する。"""
    bindings = {}
    def walk(node):
        if isinstance(node, dict):
            for key, item in node.items():
                if key in ('sources', 'source_bindings') and isinstance(item, dict):
                    for path, model in item.items():
                        if isinstance(model, dict) and type(model.get('size')) is int and 'sha256' in model:
                            expected = {k: model[k] for k in ('size', 'sha256')}
                            saved.binding(expected)
                            pair = (path, expected['sha256'])
                            bindings[pair] = expected
                else: walk(item)
        elif isinstance(node, list):
            for item in node: walk(item)
    walk(value)
    out = []
    for (path, _), expected in sorted(bindings.items()):
        p = saved.safe(root, path)
        actual = saved.identity(p.read_bytes()) if p.is_file() else None
        out.append(dict(path=path, original=expected, current=actual, unchanged=actual == expected))
    return dict(bindings=out, checked=len(out), mismatches=sum(not r['unchanged'] for r in out),
                missing_original_manifest=(not out))


def load_model(root):
    return chain_model(checked(root, NORMAL, INPUTS[NORMAL]), checked(root, GETTER, INPUTS[GETTER]))


def analyze(root):
    recipes = load_model(root); allocations = recipes[-1]['allocation']['allocations']
    receipt = saved.strict(saved.safe(root, CIRCUS).read_bytes())
    need(receipt['candidate'] == TARGET and receipt['physical_admission_accepted'] is True
         and receipt['suppression_accepted'] is True and receipt['release_ready'] is False, 'Circus receipt boundary')
    rows = {}
    for name, path in REPORTS.items():
        raw = saved.safe(root, path).read_bytes(); original = saved.strict(raw)
        candidate = {k: original['candidate'][k] for k in ('size', 'sha256')}
        row = impact(recipes, candidate, allocations)
        row.update(source_path=path, original_identity=saved.identity(raw), source_review=source_review(root, original))
        # source drift prevents unqualified same-candidate transfer.
        if row['source_review']['mismatches']:
            row['native_transfer_accepted'] = False
            row['decision'] = 'SOURCE_DRIFT_REVIEW_REQUIRED'
        rows[name] = row
    protected = [r for r in allocations if r['name'].startswith('modernization-p07')]
    need(protected, 'P07 content owners missing')
    origin = rows['P03_P06_P07']['changed_ranges']
    retained = [dict(owner=r['name'], start=r['start'], end_exclusive=r['end_exclusive'],
                     byte_preserved=not any(intersects(r['start'],r['end_exclusive'],x) for x in origin)) for r in protected]
    need(all(r['byte_preserved'] for r in retained), 'P07 content changed')
    regressions = [
        dict(id='P08_SHARED_SAVE_LOAD', scope_ja='P03既受入の保存再開代表1経路で通常Save→fresh Continue。共有save/load hook変更だけを評価。',
             owners=['SAVE_DISPATCH','LOAD_DISPATCH'], source_domain='P03_P06_P07'),
        dict(id='P08_BP_RETURN_PARTY', scope_ja='BPの代表帰還・party復元・保存再開。旧3勝/支出全件の重複実行はしない。',
             owners=['BATTLE_LOSS_RETURN','PARTY_RESTORE_CALL','FACTORY_GETTER_CALL'], source_domain='BP'),
        dict(id='P08_RING_ORDINARY', scope_ja='通常戦闘Ring代表1経路。共有保存/読込とdrought callback変更の影響を評価。',
             owners=['SAVE_DISPATCH','LOAD_DISPATCH','DROUGHT_BATTLE_CALLBACK'], source_domain='RING'),
        dict(id='P08_CIRCUS_POST_EXIT_ORDINARY', scope_ja='保存済みCircus退出後から通常戦闘へ。抑制フラグ残留がないことを自然calleeで確認。旧30勝は再実行しない。',
             owners=['DROUGHT_BATTLE_CALLBACK'], source_domain='CIRCUS'),
    ]
    for row in regressions: row.update(complete=False, new_native_processes=0)
    return dict(schema_version=1, classification='EXACT_BYTE_IMPACT_NOT_FINAL_NATIVE_ACCEPTANCE',
                candidate=TARGET, anchor=dict(path=ANCHOR_PATH, **ANCHOR),
                recipe_layers=len(recipes), patch_operations=sum(len(r['patches']) for r in recipes),
                source_bindings={p:saved.identity(saved.safe(root,p).read_bytes()) for p in (SELF,'scripts/pr16_saved_recipe.py',*INPUTS,*REPORTS.values())},
                candidate_impacts=rows, p07_content_preservation=retained,
                required_representative_regressions=regressions, old_originals_relabelled=False,
                final_native_acceptance_complete=False, final_product_sha_fixed=False, release_ready=False,
                new_emulator_processes=0, arm_compiles=0, arm_links=0, prefix_wins_reexecuted=0)


def offline(event, args):
    if (event in ('subprocess.Popen','os.system','os.posix_spawn','os.fork','os.forkpty')
            or event.startswith(('os.exec','socket.')) or event in ('urllib.Request','http.client.connect')):
        raise saved.RecipeError('offline saved-byte audit denied: '+event)


def reconstruct(root, output):
    """21層全ROM前進/逆適用を検証。旧builder、ARM、network、nativeを呼ばない。"""
    sys.addaudithook(offline)
    recipes = load_model(root)
    anchor = saved.safe(root, ANCHOR_PATH).read_bytes()
    need(saved.identity(anchor) == ANCHOR, 'fixed anchor bytes differ')
    raw, proof = saved.chain(anchor, recipes, TARGET)
    report = analyze(root)
    # 全ROM結果から疎差分projectionを独立照合。
    changes = sparse(recipes)
    for row in changes:
        a,b = row['start'],row['end_exclusive']
        need(anchor[a:b].hex()==row['before'] and raw[a:b].hex()==row['after'], 'sparse/full-ROM mismatch')
    need(saved.patch(anchor,[dict(offset=r['start'],before=r['before'],after=r['after']) for r in changes])==raw,
         'unaccounted final byte difference')
    report.update(reconstruction=proof, full_rom_sparse_comparison=True,
                  candidate_crc32=f'{zlib.crc32(raw)&0xffffffff:08X}', offline_process_barrier_active=True,
                  clean_rom_two_build_verified=False)
    relative = output.relative_to(root).as_posix()
    need(relative.startswith('.local/'), 'output must remain untracked .local')
    output = saved.safe(root, relative); output.mkdir(parents=True,exist_ok=True)
    (output/'candidate.gba').write_bytes(raw)
    (output/'impact.json').write_bytes(saved.stable(report))
    need(saved.identity(saved.safe(root, ANCHOR_PATH).read_bytes())==ANCHOR, 'anchor changed')
    return report


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('analyze','reconstruct'))
    parser.add_argument('--output',type=Path,default=ROOT/'.local/pr16-p08-impact')
    args=parser.parse_args()
    if args.command=='reconstruct': result=reconstruct(ROOT,args.output.absolute())
    else: result=analyze(ROOT)
    print(saved.stable(result).decode(),end='')
