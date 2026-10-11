#!/usr/bin/env python3
"""保存済み参照候補から有限の配置窓を順位付けする。容量leaseは発行しない。"""
from __future__ import annotations

from bisect import bisect_left
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE, ROM_END = 0x08000000, 0x0A000000
LO, HI, REQUIRED, ALIGNMENT = 0x09FED0C4, 0x09FF0BD2, 6528, 4
PARENT_ID = dict(size=5408731, sha256='f88d65c235eda330aef618776bff97037d5ca2c4c9fbea53798217dcb5bda669')
CANDIDATE = dict(size=33554432, sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
REPORT = 'content/modernization/pr16_donor_window_checkpoint.json'
PLAN = 'content/modernization/pr16_donor_window_evidence/windows.json'
CLAIMS = dict(donor_safe_bytes=0, donor_eligible=False, donor_leased=False,
    retirement_or_transfer_complete=False, indirect_reference_completeness_claimed=False,
    outside_target_excludes_access=False, intra_donor_origins_covered=False,
    native_processes=0, rom_reconstructions=0, old_full_rom_scan_runs=0,
    accepted_test_reruns=0, formal_classification_changes=0, rom_writes=0, save_writes=0)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def identity(raw):
    need(type(raw) is bytes, 'bytesのみ')
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def integer(value):
    return type(value) is int


def analyze(hits, lo, hi, required, alignment=4):
    """全整列窓を比較。点参照数は調査優先度だけで、安全性の十分条件ではない。"""
    need(all(integer(x) for x in (lo,hi,required,alignment)), '整数のみ。bool拒否')
    need(BASE <= lo < hi <= ROM_END and 0 < required <= hi-lo, 'ROM内の非空窓')
    need(alignment > 0 and alignment & (alignment-1) == 0 and alignment <= 4096,
         '整列は4096以下の2冪')
    first = ((lo+alignment-1)//alignment)*alignment
    last = ((hi-required)//alignment)*alignment
    need(first <= last, '実在する整列窓が必要')
    need((last-first)//alignment+1 <= 100000, '有限10万窓まで')
    need(type(hits) is list and len(hits) <= 10000, '有限の候補list')
    rows, seen = [], set()
    for hit in hits:
        need(type(hit) is dict, '候補はobject')
        address, target, size = (hit.get(k) for k in ('address','target','size'))
        kind, accepted, classification = (hit.get(k) for k in ('kind','accepted','classification'))
        need(all(integer(x) for x in (address,target,size)) and size == 4 and
             BASE <= address <= ROM_END-4 and lo <= target < hi, '候補の範囲/4byte型')
        need(kind in ('ALL_BYTE_START_U32_ALL_ROM_MIRRORS','THUMB_BL_SHAPE'), '保存inventoryの型')
        need(type(accepted) is bool and type(classification) is str, '正式状態の厳密型')
        need((accepted and classification.startswith('FALSE_POSITIVE_TYPED_')) or
             (not accepted and classification == 'UNCLASSIFIED'), '型受入と未知を混同しない')
        need((address,kind) not in seen, '候補重複')
        seen.add((address,kind))
        need(type(hit.get('sha256')) is str and len(hit['sha256']) == 64 and
             all(c in '0123456789abcdef' for c in hit['sha256']), '候補identity')
        rows.append(dict(address=address,target=target,size=size,kind=kind,
                         accepted=accepted,classification=classification,sha256=hit['sha256']))
    unknown = sorted((h for h in rows if not h['accepted']), key=lambda h:(h['address'],h['kind']))
    targets = sorted(h['target'] for h in unknown)
    scores = [(start,bisect_left(targets,start+required)-bisect_left(targets,start))
              for start in range(first,last+1,alignment)]
    minimum = min(score for _,score in scores)
    optimal = [start for start,score in scores if score == minimum]
    bands = []
    for start in optimal:
        if bands and start == bands[-1]['last_start']+alignment:
            bands[-1]['last_start'] = start
            bands[-1]['windows'] += 1
        else:
            bands.append(dict(first_start=start,last_start=start,windows=1))
    selected = optimal[0]
    blockers = [h for h in unknown if selected <= h['target'] < selected+required]
    excluded = [h for h in unknown if not selected <= h['target'] < selected+required]
    return dict(schema_version=1, status='FINITE_WINDOW_RANKING_NOT_A_LEASE',
        donor_range=dict(start=lo,end_exclusive=hi,size=hi-lo),required_bytes=required,alignment=alignment,
        objective='minimum_unclassified_target_entries_then_lowest_start_not_minimum_safety_risk',
        examined_windows=len(scores), first_start=first,last_start=last,
        minimum_unclassified_target_entries=minimum, optimal_start_bands=bands,
        score_histogram=[dict(unclassified_target_entries=k,windows=v) for k,v in sorted(Counter(s for _,s in scores).items())],
        selected=dict(start=selected,end_exclusive=selected+required,size=required,
            unclassified_target_entries=len(blockers),distinct_unclassified_targets=len({h['target'] for h in blockers}),
            accepted_false_positive_entries=sum(h['accepted'] and selected <= h['target'] < selected+required for h in rows),
            unclassified_target_rows=blockers),
        inherited=dict(total=len(rows),classified=sum(h['accepted'] for h in rows),unclassified=len(unknown)),
        outside_point_count=len(excluded),outside_point_rows_still_unresolved=True,
        claims=copy.deepcopy(CLAIMS),
        limitations_ja=[
            '対象は保存inventoryの正規化済みtarget点。窓外からの長さ付きread/計算参照/ROM mirrorを安全側で除外しない。',
            '旧inventoryは15118byte内に全体が収まるoriginを除外したため、部分窓内外の参照完全性は未証明。',
            'acceptedは元の有限条件付き型証拠の継承であり、全実行状態の非参照証明ではない。',
            '同点は最小addressで固定。選定窓は調査範囲であり配置承認・owner退役・保存成功ではない。'])


def bind_parent(audit, canonical):
    """独立して固定した全親hashと正式状態が合わない入力を拒否する。"""
    need(identity(canonical(audit)) == PARENT_ID, '正式Forest親全identity')
    need(audit['candidate'] == CANDIDATE and
         [audit['classified'],audit['unclassified'],len(audit['hits'])] == [785,89,874], '候補/正式件数')
    need(audit['donor_eligible'] is False and audit['donor_leased'] is False and
         audit['indirect_reference_completeness_claimed'] is False, 'lease/完全性の昇格禁止')
    old, live = audit['retired_candidate'], audit['current_replacement']
    need([old['address'],old['size']] == [LO,HI-LO] and
         [live['address'],live['size']] == [0x095D9EFC,15396] and audit['current_scan_limit'] == 7696,
         '保存旧owner/現行置換先')
    need([r['address'] for r in audit['active_roots']] == [BASE+0x45214,BASE+0x4528C] and
         all(r['points_to'] == live['address'] for r in audit['active_roots']), '既知root2件')
    result = analyze(audit['hits'],LO,HI,REQUIRED,ALIGNMENT)
    need(result['inherited'] == dict(total=874,classified=785,unclassified=89), '全874候補を維持')
    result.update(parent_audit_identity=copy.deepcopy(PARENT_ID),candidate=copy.deepcopy(CANDIDATE),
        recorded_owners=dict(old=dict(address=LO,size=HI-LO),replacement=dict(address=live['address'],size=live['size']),
            active_roots=copy.deepcopy(audit['active_roots']),current_scan_limit=7696,
            whole_owner_retirement_proven=False,partial_window_transfer_proven=False))
    return result


def from_saved(root=ROOT):
    # 保存原本の復元だけ。旧測定器/ROM inventory/reader/nativeは呼ばない。
    from pr16_forest_wallpaper_receipt import restore_parent
    from pr16_dex_hof_blastoise_chain import canonical
    audit = restore_parent(root)
    return bind_parent(audit,canonical)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='保存済み計画を読取専用照合')
    args = parser.parse_args()
    raw = encode(from_saved())
    if args.check:
        path = ROOT/PLAN
        need(path.is_file() and not path.is_symlink() and path.read_bytes() == raw, '保存計画不一致')
        print('PASS_SAVED_WINDOW_PLAN_READ_ONLY donor_safe_bytes=0')
    else:
        import sys
        sys.stdout.buffer.write(raw)
