"""P08の過去記録を保存したまま、現在の受入残件を検証・生成する。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import modernization_p08_stage79_evidence as evidence  # noqa: E402
from tools import modernization_p08_representative_evidence as representative  # noqa: E402
from tools import modernization_p08_stage81_evidence as native  # noqa: E402

OUTPUT = 'content/modernization/p08_current_acceptance.json'
DOCUMENTS = tuple(f'content/modernization/p08_{name}.json' for name in
                  ('integration_matrix', 'runtime_handoff', 'release_handoff'))
P06 = 'content/modernization/p06_species_adjustment_contract.json'
P07 = 'content/modernization/p07_layered_learnset_contract.json'
P07_HANDOFF = 'content/modernization/p07_runtime_handoff.json'
ECONOMY = 'config/modernization_p03_stage74_supply.json'
ADDITIVE_KEYS = {'historical_checkpoint_scope', 'current_cumulative_runtime',
                 'cumulative_evidence_binding'} | representative.KEYS | native.KEYS


def boolean(record: dict[str, Any], key: str) -> bool:
    value = record.get(key)
    evidence.require(type(value) is bool, f'boolean missing or invalid: {key}')
    return value


def count(record: dict[str, Any], key: str) -> int:
    value = record.get(key)
    evidence.require(type(value) is int and value >= 0, f'invalid count: {key}')
    return value


def build_report(root: Path = ROOT) -> dict[str, Any]:
    """読み取り専用。通常CIの成功や関数単体PASSを製品受入へ昇格しない。"""
    current = evidence.build_extension(root)
    representative_e2e = representative.build_extension(root)
    native_acceptance = native.build_extension(root)
    sources: dict[str, dict[str, Any]] = dict(representative_e2e['source_bindings'])

    if native_acceptance is not None:
        sources.update(native_acceptance['source_bindings'])

    def load(path: str) -> dict[str, Any]:
        raw = evidence.regular(root, path)
        sources[path] = {'sha256': evidence.sha(raw), 'size': len(raw)}
        result = json.loads(raw)
        evidence.require(isinstance(result, dict), f'JSON object required: {path}')
        return result

    historical: dict[str, Any] = {}
    for path in DOCUMENTS:
        document = load(path)
        native.validate_document(document, native_acceptance)
        representative.validate_document(native.strip(document), representative_e2e)
        evidence.require(document.get('release_ready') is False,
                         f'unapproved release promotion: {path}')
        evidence.require(document.get('current_cumulative_runtime') == current,
                         f'stale current runtime extension: {path}')
        evidence.require(isinstance(document.get('historical_checkpoint_scope'), str)
                         and document['historical_checkpoint_scope'].startswith('Stage77 '),
                         f'historical scope missing: {path}')
        original = {k: v for k, v in document.items() if k not in ADDITIVE_KEYS}
        digest = evidence.sha(evidence.stable(original))
        binding = {'historical_document_sha256': digest,
                   'sha256': evidence.sha(evidence.stable({
                       'historical_document_sha256': digest,
                       'current_cumulative_runtime': current}))}
        evidence.require(document.get('cumulative_evidence_binding') == binding,
                         f'historical/runtime binding mismatch: {path}')
        if path == DOCUMENTS[0]:
            historical = original

    for current in ([current, native_acceptance] if native_acceptance is not None else [current]):
        evidence.require(isinstance(current.get('claims'), dict)
                         and set(current['claims']) == set(evidence.CLAIMS)
                         and all(value is False for value in current['claims'].values())
                         and current.get('phase_completion_promoted') is False,
                         'unsupported phase or release promotion')
        rows = current.get('domains', [])
        evidence.require([row.get('id') for row in rows] == list(evidence.DOMAINS),
                         'current domain set mismatch')
        results: dict[str, dict[str, Any]] = {}
        for row in rows:
            record = load(row['result_path'])
            evidence.require(sources[row['result_path']]['sha256'] == row['result_sha256'],
                             f'result digest mismatch: {row["id"]}')
            evidence.require(record.get('id') == row['id'] and record.get('status') == 'PASS'
                             and record.get('input_rom') == current['candidate_rom']
                             and record.get('plan_fingerprint') == current['plan_fingerprint'],
                             f'result identity mismatch: {row["id"]}')
            results[row['id']] = record['runner_result']

    blockers: list[dict[str, Any]] = []

    def blocked(identifier: str, phase: str, reason: str, source: str, pointer: str) -> None:
        blockers.append({'id': identifier, 'phase': phase, 'reason_ja': reason,
                         'source_path': source, 'source_pointer': pointer})

    limits = {}
    definitions = {
        'p03': {'scheduler_e2e': '通常習得・進化キャンセルの代表2ケースはPASS。満杯時の技入替・拒否、他の習得画面や育成経路の通し検証は未完了',
                'breeding_e2e': '預かり屋・タマゴ生成を通した検証が未完了',
                'save_reload_e2e': '通常習得後の保存・新規core Continueは代表2ケースでPASS。他の習得経路での保存・再読込は未完了',
                'full_p03_acceptance': 'P03全体の受入が未完了'},
        'p05': {'scheduler_e2e': '6特性24条件とDragonize操作観測4条件はPASS。その他の技・特性経路、自然な特性取得・Battle Circus入場を含む全体検証は未完了',
                'full_p05_acceptance': 'P05全体の受入が未完了'},
    }
    if native_acceptance is not None:
        definitions['p03']['scheduler_e2e'] = 'Stage81で満杯4枠の入替・拒否・キャンセル・空き枠・対照の8ケースはPASS。他の習得画面や育成経路の通し検証は未完了'
        definitions['p03']['save_reload_e2e'] = 'Stage81の代表8ケースで通常保存・新規core Continue・技とPPの復元はPASS。他の習得経路の保存・再読込は未完了'
        definitions['p05']['scheduler_e2e'] = 'Stage80の6特性24条件とDragonize操作観測4条件は履歴として保持。Stage81では既存P05 runnerがPASS。新候補のその他の戦闘経路・自然な特性取得・Mega・Circus入場の通し受入は未完了'
    for domain, fields in definitions.items():
        limits[domain] = {key: boolean(results[domain], key) for key in fields}
        path = next(row['result_path'] for row in rows if row['id'] == domain)
        for key, reason in fields.items():
            if not limits[domain][key]:
                identifier = f'{domain.upper()}_{key.upper()}_PENDING'.replace(
                    f'FULL_{domain.upper()}_', 'FULL_')
                blocked(identifier, domain.upper(),
                        reason, path, f'/runner_result/{key}')
    # この既存完了項目を過去のStage77残件から復活させない。
    evidence.require(boolean(results['p05'], 'eelevate_switch_ai_done'),
                     'Eelevate switch AI is no longer evidenced as complete')

    economy = load(ECONOMY)['runtime']['economy']
    evidence.require(economy.get('status') == 'PROVISIONAL_REPLACEABLE',
                     'archive economy changed: explicit acceptance policy update required')
    blocked('P03_ARCHIVE_ECONOMY_PROVISIONAL', 'P03', 'archive economyの正式仕様が未確定',
            ECONOMY, '/runtime/economy')

    p06 = load(P06)
    adoption = p06['adoption']
    n06 = count(adoption, 'adopted_delta_count')
    evidence.require(isinstance(adoption.get('adopted_delta_records'), list)
                     and n06 == len(adoption['adopted_delta_records']), 'P06 adoption count mismatch')
    evidence.require(n06 == 0 and boolean(adoption, 'explicit_species_adjustment_spec_received') is False
                     and boolean(adoption, 'runtime_patch_authorized') is False,
                     'P06 adoption changed: explicit runtime acceptance policy required')
    review = p06['review_partition']
    projection = load(review['projection_path'])
    evidence.require(sources[review['projection_path']]['sha256'] == review['projection_sha256']
                     and count(review, 'source_record_count') == len(projection['records']),
                     'P06 review provenance/count mismatch')
    blocked('P06_SPECIES_ADJUSTMENT_NOT_ADOPTED', 'P06',
            'レビュー資料は採用指示ではない。正式な種族・フォーム・field単位の採用仕様が必要',
            P06, '/adoption')

    p07 = load(P07)
    p07_handoff = load(P07_HANDOFF)
    summary = p07['summary']
    evidence.require(p07_handoff.get('summary') == summary
                     and p07_handoff.get('runtime_handoff') == p07['runtime_handoff'],
                     'P07 contract/handoff disagreement')
    for key, summary_key in (
        ('normal_species_to_vega_move', 'normal_species_to_vega_move_adopted'),
        ('vega_species_to_normal_move', 'vega_species_to_normal_move_adopted'),
        ('explicit_deletions', 'explicit_deletions_adopted')):
        entries = p07['adopted_delta'].get(key)
        evidence.require(isinstance(entries, list) and count(summary, summary_key) == len(entries),
                         f'P07 adopted count mismatch: {key}')
        evidence.require(not entries, 'P07 adoption changed: explicit runtime acceptance policy required')
    evidence.require(p07['adopted_delta'].get('invented_rows') == [], 'P07 invented distribution rows')
    evidence.require(boolean(summary, 'runtime_implemented') is False
                     and boolean(summary, 'p06_ready') is False
                     and boolean(p07['runtime_handoff'], 'runtime_implemented') is False,
                     'P07 runtime/phase promotion without acceptance evidence')
    blocked('P07_CROSS_DISTRIBUTION_NOT_ADOPTED', 'P07',
            '双方向の技配布の採用仕様・P06整合・実装・画面と保存を含む検証が未完了',
            P07, '/runtime_handoff')
    blocked('P08_FINAL_ACCEPTANCE_AND_RELEASE_DECISION_PENDING', 'P08',
            '各工程の最終受入とリリース判定が未完了。Stage62基準を自動昇格しない',
            DOCUMENTS[2], '/release_ready')

    return {
        'schema_version': 1,
        'task': 'USER-MODERNIZATION-P08-CURRENT-ACCEPTANCE',
        'validation_status': 'PASS',
        'acceptance_status': 'BLOCKED',
        'release_ready': False,
        'candidate_rom': current['candidate_rom'],
        'candidate_stage': current['candidate_stage'],
        'active_baseline_stage': current['active_baseline_stage'],
        'active_baseline_changed': False,
        'phase_completion_promoted': False,
        'heavy_execution_performed': False,
        'runtime_evidence_source': current['source'],
        'plan_fingerprint': current['plan_fingerprint'],
        'satisfied_runtime_domains': [row['id'] for row in rows],
        'eelevate_switch_ai_done': True,
        'declared_runtime_limits': limits,
        'declared_runtime_limits_scope': 'UNCHANGED_ORIGINAL_STAGE79_FLAGS_NOT_REPRESENTATIVE_PROGRESS',
        'representative_e2e': representative_e2e,
        **({'native_pp_acceptance': native_acceptance,
            'representative_e2e_scope': 'STAGE80_HISTORY_NOT_RECOUNTED_AS_STAGE81'} if native_acceptance is not None else {}),
        'unclaimed_coverage': {key: current['claims'][key] for key in
                              ('link_runtime_e2e', 'physical_all_menu_paths_e2e')},
        'p06_adoption': {'review_record_count': review['source_record_count'], 'adopted_delta_count': n06},
        'p07_adoption': {key: summary[key] for key in
                        ('normal_species_to_vega_move_adopted', 'vega_species_to_normal_move_adopted',
                         'explicit_deletions_adopted', 'runtime_implemented')},
        'current_blockers': blockers,
        'historical_stage77': {'scope': 'HISTORICAL_ONLY_NOT_CURRENT_BLOCKER_LIST',
                               'source_path': DOCUMENTS[0],
                               'release_blockers': historical['release_blockers'],
                               'modified': False},
        'source_bindings': sources,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--write', action='store_true', help='現在の受入スナップショットを明示的に書き込む')
    mode.add_argument('--check', action='store_true', help='既存スナップショットとの完全一致を確認する（読み取り専用）')
    parser.add_argument('--require-release-ready', action='store_true', help='受入残件がある場合は非zeroで終了する')
    args = parser.parse_args(argv)
    try:
        report = build_report()
        raw = evidence.stable(report)
        if args.write:
            target = ROOT / OUTPUT
            evidence.require(not target.is_symlink(), 'refuse symlink output')
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(raw)
                temporary.replace(target)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        if args.check:
            evidence.require(evidence.regular(ROOT, OUTPUT) == raw, 'current acceptance snapshot is stale')
        sys.stdout.buffer.write(raw)
        return 1 if args.require_release_ready and report['release_ready'] is not True else 0
    except (evidence.EvidenceError, KeyError, TypeError, ValueError, OSError) as error:
        print(f'P08 current acceptance validation failed: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
