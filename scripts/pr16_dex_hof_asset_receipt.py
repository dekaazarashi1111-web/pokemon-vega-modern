#!/usr/bin/env python3
"""新Diploma成功runの保存4原本だけを受入。ROM/consumer/旧suiteは再走しない。"""
from __future__ import annotations

import copy
import io
import json
import re
import stat
import zipfile
from pathlib import Path

import pr16_dex_hof_diploma_validation as validation
import pr16_dex_hof_diploma_chain as chain
import pr16_dex_hof_diploma_asset as field

ROOT = Path(__file__).resolve().parents[1]
CP = 'content/modernization/pr16_dex_hof_diploma_checkpoint.json'
EVIDENCE = 'content/modernization/pr16_dex_hof_diploma_evidence'
FRONTIER = EVIDENCE + '/unknown-frontier.json'
OLD_FRONTIER = 'content/modernization/pr16_dex_hof_jp_minigame_evidence/unknown-frontier.json'
GUIDE = 'docs/PR16_DEX_HOF_DIPLOMA_ACCEPTED_JA.md'
HEAD = '60f32297e1a20266f8e5638df66dea28901cf84d'
RUN = 37718308112
JOB = 113119846893
ARTIFACT_NAME = 'pr16-diploma-asset-only'
# 成功artifact実取得・生成/検証/公開前logの12hash照合済みidentityだけを固定する。
FILES = {'measurement.json': {'sha256': '9d15682887a459c8c5118b8b5e9e0feecf9416250e7e143bd95502bfaae98e52',
                      'size': 43872},
 'provenance.json': {'sha256': '3e0e351216bbb883f6cda8e21ecbf37cb79f60ae6f5bdd24ba79715058edb676',
                     'size': 13362},
 'reference-chain.json': {'sha256': '017219a26f87021cafdf48f1f6fe9064a021421bb856685ade710c6ce743c7fc',
                          'size': 26250},
 'tests.json': {'sha256': '947a2088691beb8247138d82d6a00aaf4c47bf80aca2b6dbf64092413b2da170', 'size': 141}}
ARTIFACT_ID = 11524203520
ZIP_SIZE = 23805
ZIP_SHA = 'b26e3f9067fe58caf99306e3a544671e77b79bcf36fda685c42ed2ec485b50f6'
ARTIFACT_TIMES = {'created_at': '2026-10-08T02:34:50Z', 'expires_at': '2027-01-06T02:31:40Z', 'updated_at': '2026-10-08T02:34:50Z'}
JOB_LOG_ID = {'size': 28116, 'sha256': '4c3846b82023b9e590e6b63422942f9c5700ff98c0c33b34a20e5f222521e72e'}
need, identity, exact = field.need, field.identity, validation.exact
COUNTERS = dict(
    schema_version=1, classified=783, unclassified=91, newly_classified=1,
    inherited_classified=782, inherited_unclassified=92, unit_tests=168,
    old_scope_test_reruns=0, current_rom_reconstructions=1, current_owner_count=115,
    saved_hit_count=874, inherited_parent_inputs=57, inherited_namespaces=29,
    inherited_changes=163, inherited_witnesses=153, source_file_count=14,
    public_source_file_count=13, accepted_namespaces=30, accepted_changes=164,
    accepted_witnesses=154, native_processes=0, donor_safe_bytes=0,
    old_full_rom_scan_runs=0, old_native_cases_replayed=0,
    formal_rom_changed=False, formal_save_changed=False, donor_eligible=False,
    donor_leased=False, release_ready=False, conditional_finite_type_only=True,
    actual_runtime_execution_observed=False, actual_bios_cpu_executed=False,
    actual_screen_rendered=False, full_story_reachability_claimed=False,
    opaque_callee_effects_proven=False, universal_heap_or_irq_lifetime_proven=False,
    indirect_reference_completeness_claimed=False, padding_classified=False,
    reconstructed_text_promoted_as_original=False,
    all_prior_accepted_retained=True, remaining_unknown_rows_retained=True)
LOG_FIELDS = ('generated_file_identities', 'validated_file_identities', 'published_file_identities')
RECEIPT_FIELDS = frozenset(COUNTERS) | frozenset({
    'status', 'source_head', 'run_id', 'run_attempt', 'conclusion', 'job', 'artifact',
    'candidate', 'evidence_bindings', 'delta_identity', 'measurement_identity',
    'tests_identity', 'provenance_identity', 'unknown_identity', 'job_log_identity',
    'guide', 'previous_checkpoint', 'next_ja', *LOG_FIELDS})
STEP_NAMES = [
    'Set up job', 'Run actions/checkout@v4',
    'First scope across all branches and closed source boundary',
    'Official Ubuntu compiler for current candidate',
    'New Diploma source-exact LZ10 and actual consumer only',
    'Closed successful text publication guard', 'Run actions/upload-artifact@v4',
    'Post Run actions/checkout@v4', 'Complete job']
STEP_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 14, 15]


def _pins_ready():
    need(type(FILES) is dict and set(FILES) == validation.FILES and
         all(validation.valid_identity(value) for value in FILES.values()) and
         type(ARTIFACT_ID) is int and ARTIFACT_ID > 0 and
         type(ZIP_SIZE) is int and ZIP_SIZE > 0 and type(ZIP_SHA) is str and
         re.fullmatch(r'[0-9a-f]{64}', ZIP_SHA) is not None and
         validation.valid_identity(JOB_LOG_ID) and type(ARTIFACT_TIMES) is dict and
         set(ARTIFACT_TIMES) == {'created_at', 'expires_at', 'updated_at'} and
         all(type(value) is str and re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', value)
             for value in ARTIFACT_TIMES.values()),
         '成功4原本/取得ZIP/全job logの実取得identity確定前は受入不可')


def verify_artifact_zip(raw):
    """実取得ZIP全byteとflatな4原本を検証し、未承認の余剰fileを拒否する。"""
    _pins_ready()
    need(type(raw) is bytes and exact(identity(raw), dict(size=ZIP_SIZE, sha256=ZIP_SHA)),
         '取得artifact ZIPの全byte identity')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        need(len(entries) == 4 and {entry.filename for entry in entries} == set(FILES),
             'ZIP内部はflatな4原本だけ。重複/余剰/欠落/pathを拒否')
        need(all(not entry.is_dir() and not stat.S_ISLNK(entry.external_attr >> 16) and
                 not entry.flag_bits & 1 and exact(entry.file_size, FILES[entry.filename]['size'])
                 for entry in entries), '暗号化/symlink/異常sizeの原本を拒否')
        files = {name: archive.read(name) for name in sorted(FILES)}
    need(all(exact(identity(files[name]), expected) for name, expected in FILES.items()),
         'ZIPから取得した4原本の完全byte identity')
    return files


def verify_job_log(raw):
    """取得log全byteを認証し、生成1組・検証1組・公開前1組の全4hashを照合。"""
    _pins_ready()
    need(type(raw) is bytes and exact(identity(raw), JOB_LOG_ID), '取得job log完全identity')
    records = []
    statuses = {'GENERATED_DIPLOMA_FILE_IDENTITY', 'PASS_DIPLOMA_PUBLIC_FILE'}
    for line in raw.decode('utf-8').splitlines():
        start = line.find('{')
        if start < 0:
            continue
        try:
            value = json.loads(line[start:], object_pairs_hook=validation._unique_object,
                               parse_constant=validation._invalid_constant,
                               parse_float=validation._invalid_constant)
        except json.JSONDecodeError:
            need(not any(status in line for status in statuses), 'identity行の不正JSONを拒否')
            continue
        if type(value) is not dict or value.get('status') not in statuses:
            continue
        need(set(value) == {'status', 'file', 'size', 'sha256'} and
             type(value['file']) is str and value['file'] in FILES and
             exact({key: value[key] for key in ('size', 'sha256')}, FILES[value['file']]),
             '全log行の閉schemaと取得4原本identity')
        records.append(value)
    expected = [dict(status=status, file=name, **FILES[name])
                for status in ('GENERATED_DIPLOMA_FILE_IDENTITY',
                               'PASS_DIPLOMA_PUBLIC_FILE', 'PASS_DIPLOMA_PUBLIC_FILE')
                for name in sorted(FILES)]
    need(exact(records, expected), '生成/検証/公開前の順序と各4fileを過不足なく保持')
    return dict(job_log_identity=copy.deepcopy(JOB_LOG_ID),
                **{key: copy.deepcopy(FILES) for key in LOG_FIELDS})


def unknown_frontier(full, old):
    """旧92行から083DCAEDだけを除き、他91行の全fieldと順序を保存する。"""
    need(type(old) is dict and set(old) == {
        'candidate', 'total', 'owner_unknown', 'unowned_unknown', 'rows',
        'donor_eligible', 'indirect_reference_completeness_claimed'}, '旧frontierの閉schema')
    need(exact(old['candidate'], field.CANDIDATE) and exact(full['candidate'], field.CANDIDATE) and
         exact([old['total'], old['owner_unknown'], old['unowned_unknown']], [92, 0, 92]) and
         old['donor_eligible'] is False and old['indirect_reference_completeness_claimed'] is False,
         '旧92unknownの厳密counter/候補/安全claim')
    need(type(old['rows']) is list and len(old['rows']) == 92 and
         all(type(row) is dict and set(row) == {'hit', 'owners'} and
             type(row['hit']) is dict and exact(row['owners'], []) for row in old['rows']),
         '旧92行の閉schemaとowner外を保持')
    rows = [row for row in old['rows'] if row['hit']['address'] != field.HIT]
    need(len(rows) == 91, '唯一の新4byte型だけをunknownから除く')
    need(exact([full['classified'], full['unclassified']], [783, 91]) and
         exact([row['hit'] for row in rows], [hit for hit in full['hits'] if hit['accepted'] is False]),
         '正式deltaの全91unknownと旧行の全field/順序が一致')
    result = copy.deepcopy(old)
    result.update(total=91, owner_unknown=0, unowned_unknown=91, rows=copy.deepcopy(rows))
    return result


def _successful_metadata(receipt):
    job = dict(id=JOB, name='diploma-asset', status='completed', conclusion='success',
               run_id=RUN, logs_url=None, steps=[
                   dict(name=name, status='completed', conclusion='success', number=number)
                   for name, number in zip(STEP_NAMES, STEP_NUMBERS)])
    need(exact(receipt['job'], job), '同source jobと全9stepの成功終端/順序/型')
    url = ('https://api.github.com/repos/dekaazarashi1111-web/pokemon-vega-modern/'
           'actions/artifacts/' + str(ARTIFACT_ID))
    artifact = dict(id=ARTIFACT_ID, name=ARTIFACT_NAME, size_in_bytes=ZIP_SIZE,
                    url=url, archive_download_url=url + '/zip', expired=False,
                    digest='sha256:' + ZIP_SHA, **ARTIFACT_TIMES, workflow_run=dict(
                        id=RUN, repository_id=1358127462, head_repository_id=1358127462,
                        head_branch='codex/modernization-followup-20260908', head_sha=HEAD))
    need(exact(receipt['artifact'], artifact), '外側ZIP/取得時刻と同repository/branch/run/sourceの閉identity')


def validate(receipt, files, frontier, root=ROOT):
    """外部取得も測定もせず、保存済み原本・source・receipt・frontierを照合する。"""
    _pins_ready()
    need(type(files) is dict and set(files) == set(FILES), '成功artifactの閉4fileだけ')
    need(all(type(files[name]) is bytes and exact(identity(files[name]), expected)
             for name, expected in FILES.items()), '成功4原本の完全byte identity')
    need(type(receipt) is dict and set(receipt) == RECEIPT_FIELDS, '閉じた受入receipt schema')
    for key, value in COUNTERS.items():
        need(exact(receipt[key], value), '厳密な受入counter/flag: ' + key)
    for key, value in dict(status='ACCEPTED_ONE_DIPLOMA_MINIMUM_ASSET_TYPE', source_head=HEAD,
                           run_id=RUN, run_attempt=1, conclusion='success', candidate=field.CANDIDATE,
                           guide=GUIDE, previous_checkpoint=chain.PARENT_CHECKPOINT).items():
        need(exact(receipt[key], value), '成功identity/guide/親checkpoint: ' + key)
    need(type(receipt['next_ja']) is str and bool(receipt['next_ja'].strip()), '次工程の明記')
    _successful_metadata(receipt)
    need(exact(receipt['job_log_identity'], JOB_LOG_ID) and
         all(exact(receipt[key], FILES) for key in LOG_FIELDS), '生成/検証/公開前logの全4hashを保持')
    need(exact(receipt['evidence_bindings'], {EVIDENCE + '/' + name: value
                                            for name, value in FILES.items()}), '保存4原本の参照binding')
    for key, name in (('delta_identity', 'reference-chain.json'), ('measurement_identity', 'measurement.json'),
                      ('tests_identity', 'tests.json'), ('provenance_identity', 'provenance.json')):
        need(exact(receipt[key], FILES[name]), '保存原本の完全identity: ' + key)
    root = Path(root)
    need(len(chain.PARENT_INPUTS) == 57 and len(validation.SOURCE_CODE) == 14 and
         len(validation.sources.SOURCE_IDS) == 13,
         '全57保存親原本と閉14内部source/13公開source境界')
    parent = chain.parent(*[(root / path).read_bytes() for path in chain.PARENT_INPUTS])
    need(exact([parent['classified'], parent['unclassified']], [782, 92]) and
         len(chain.INHERITED_NAMES) == 29 and
         sum(len(parent[name]['changes']) for name in chain.INHERITED_NAMES) == 163 and
         sum(len(parent[name]['witnesses']) for name in chain.INHERITED_NAMES) == 153,
         '正式782/92親と全29段163変更153witnessを保持')
    source_bindings = {path: identity((root / path).read_bytes()) for path in sorted(validation.SOURCE_CODE)}
    values = {name: validation.read_text(raw) for name, raw in files.items()}
    report = values['measurement.json']
    validation.validate_report(report, files['reference-chain.json'], parent, source_head=HEAD,
                               run_id=RUN, expected_bindings=source_bindings, test_count=168)
    need(exact(values['tests.json'], validation.test_summary(168)), '新168成功原本継承/旧suite再走0')
    need(exact(values['provenance.json'], validation.provenance(report)),
         '現在実測と独立疎fixtureを厳密に分離')
    delta = chain.read_measured(files['reference-chain.json'], FILES['reference-chain.json'], parent)
    full = chain.materialize(parent, delta)
    names = (*chain.INHERITED_NAMES, chain.NAMESPACE)
    need(set(full) == set(parent) | {chain.NAMESPACE} and
         exact(full[chain.NAMESPACE], delta) and len(names) == 30 and
         sum(len(full[name]['changes']) for name in names) == 164 and
         sum(len(full[name]['witnesses']) for name in names) == 154,
         '唯一の新namespaceと正式30段164変更154witness')
    old_raw = (root / OLD_FRONTIER).read_bytes()
    checkpoint = validation.read_text((root / chain.PARENT_CHECKPOINT).read_bytes())
    need(exact(identity(old_raw), checkpoint['unknown_identity']), '親checkpointが束縛する旧92unknown原本')
    expected_frontier = unknown_frontier(full, validation.read_text(old_raw))
    need(exact(frontier, expected_frontier), '旧残91行の削除/改作/再順序/安全昇格を拒否')
    need(exact(receipt['unknown_identity'], identity(chain.canonical(frontier))), '残91unknownの完全identity')
    need(len(parent['hits']) == len(full['hits']) == 874 and
         all(exact(old, new) for old, new in zip(parent['hits'], full['hits']) if old['address'] != field.HIT),
         '他873行の全fieldと順序を保持')
    need(all(exact(full[key], value) for key, value in parent.items()
             if key not in {'hits', 'classified', 'unclassified', 'classifications'}),
         '全既受入namespace/source binding/安全claimを保持')
    return dict(status='PASS_RETAINED_783_CLASSIFIED_91_UNKNOWN', classified=783, unclassified=91,
                newly_classified=1, native_processes=0, measurement_replays=0,
                old_scope_test_reruns=0, donor_safe_bytes=0)


def main():
    _pins_ready()
    receipt = validation.read_text((ROOT / CP).read_bytes())
    directory = ROOT / EVIDENCE
    need({path.name for path in directory.iterdir()} == set(FILES) | {'unknown-frontier.json'},
         '受入保存directoryは4原本と91unknownだけ。余剰raw/bytehexを拒否')
    files = {name: validation.read_regular(directory / name) for name in FILES}
    frontier = validation.read_text((ROOT / FRONTIER).read_bytes())
    print(json.dumps(validate(receipt, files, frontier), sort_keys=True))


if __name__ == '__main__':
    main()
