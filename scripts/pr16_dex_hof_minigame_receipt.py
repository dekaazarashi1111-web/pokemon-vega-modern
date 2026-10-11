#!/usr/bin/env python3
"""新minigame成功runの保存4原本だけを受入。ROM/consumer/旧suiteは再走しない。"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pr16_dex_hof_jp_minigame_validation as validation
import pr16_dex_hof_jp_minigame_chain as chain
import pr16_dex_hof_jp_minigame_text as field

ROOT = Path(__file__).resolve().parents[1]
CP = 'content/modernization/pr16_dex_hof_jp_minigame_checkpoint.json'
EVIDENCE = 'content/modernization/pr16_dex_hof_jp_minigame_evidence'
FRONTIER = EVIDENCE + '/unknown-frontier.json'
OLD_FRONTIER = 'content/modernization/pr16_dex_hof_jp_item_evidence/unknown-frontier.json'
GUIDE = 'docs/PR16_DEX_HOF_MINIGAME_ACCEPTED_JA.md'
HEAD = 'cde7da732b17ba3dbc4806ea87680b2ca012b9c6'
RUN = 37713083180
JOB = 113103259904
ARTIFACT_NAME = 'pr16-jp-minigame-text-only'
# 成功artifact実取得・生成/検証/公開前log一致後だけ実identityへ置換する。
FILES = {'measurement.json': {'size': 1033412, 'sha256': '40e6ce79fc92557dc8c35ee1ae0d5b01c68cc36f599c668e63a159904585077f'}, 'provenance.json': {'size': 1712, 'sha256': '835a1131ec10bae3387893b42e6f047319b292141a42476b95a09a6ba8dd5581'}, 'reference-chain.json': {'size': 428715, 'sha256': 'b2a22b8fa00ef667fb04c889a7661cf34fe20d2ab9e4b9c6906a43a2c97f1263'}, 'tests.json': {'size': 142, 'sha256': '78981cfde9a792d7ac554a5f7cdac728187c48ba6ff50d950ed4fb30eeecf77e'}}
ARTIFACT_ID = 11522331925
ZIP_SIZE = 119856
ZIP_SHA = '1c4f5d8191bf6a704b4aba0e8cc488dba9d5ac6e8daa300e7383318afcdb744b'
ARTIFACT_TIMES = {'created_at': '2026-10-08T01:31:04Z', 'expires_at': '2027-01-06T01:28:15Z', 'updated_at': '2026-10-08T01:31:04Z'}
JOB_LOG_ID = {'size': 28539, 'sha256': '4d23fad38b7ed4c19b131f8e95680c2c4aa69db2f6bab491563576f480273a74'}
need, identity, exact = field.need, field.identity, validation.exact
COUNTERS = dict(
    schema_version=1, classified=782, unclassified=92, newly_classified=1,
    inherited_classified=781, inherited_unclassified=93, unit_tests=152,
    old_scope_test_reruns=0, current_rom_reconstructions=1, current_owner_count=115,
    saved_hit_count=874, inherited_parent_inputs=55, inherited_namespaces=28,
    inherited_changes=162, inherited_witnesses=152, source_file_count=14,
    native_processes=0, donor_safe_bytes=0, old_full_rom_scan_runs=0,
    old_native_cases_replayed=0, formal_rom_changed=False, formal_save_changed=False,
    donor_eligible=False, donor_leased=False, release_ready=False,
    actual_runtime_execution_observed=False, reconstructed_text_promoted_as_original=False,
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
    'New minigame rejection and cancellation roots with complete text only',
    'Closed successful text publication guard', 'Run actions/upload-artifact@v4',
    'Read-only checkout and task graph', 'Post Run actions/checkout@v4', 'Complete job']
STEP_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 8, 16, 17]


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


def verify_job_log(raw):
    """取得log全byteを認証し、生成1組・検証1組・公開前1組の全4hashを照合。"""
    _pins_ready()
    need(type(raw) is bytes and exact(identity(raw), JOB_LOG_ID), '取得job log完全identity')
    records = []
    statuses = {'GENERATED_MINIGAME_FILE_IDENTITY', 'PASS_MINIGAME_PUBLIC_FILE'}
    for line in raw.decode('utf-8').splitlines():
        start = line.find('{')
        if start < 0:
            continue
        try:
            value = json.loads(line[start:], object_pairs_hook=validation._unique_object,
                               parse_constant=validation._invalid_constant)
        except json.JSONDecodeError:
            continue
        if type(value) is not dict or value.get('status') not in statuses:
            continue
        need(set(value) == {'status', 'file', 'size', 'sha256'} and
             type(value['file']) is str and value['file'] in FILES and
             exact({key: value[key] for key in ('size', 'sha256')}, FILES[value['file']]),
             '全log行の閉schemaと取得4原本identity')
        records.append(value)
    expected = [dict(status=status, file=name, **FILES[name])
                for status in ('GENERATED_MINIGAME_FILE_IDENTITY',
                               'PASS_MINIGAME_PUBLIC_FILE', 'PASS_MINIGAME_PUBLIC_FILE')
                for name in sorted(FILES)]
    need(exact(records, expected), '生成/検証/公開前の順序と各4fileを過不足なく保持')
    return dict(job_log_identity=copy.deepcopy(JOB_LOG_ID),
                **{key: copy.deepcopy(FILES) for key in LOG_FIELDS})


def unknown_frontier(full, old):
    """旧93行から083DE6ABだけを除き、他92行の全fieldと順序を保存する。"""
    need(type(old) is dict and set(old) == {
        'candidate', 'total', 'owner_unknown', 'unowned_unknown', 'rows',
        'donor_eligible', 'indirect_reference_completeness_claimed'}, '旧frontierの閉schema')
    need(exact(old['candidate'], field.CANDIDATE) and exact(full['candidate'], field.CANDIDATE) and
         exact([old['total'], old['owner_unknown'], old['unowned_unknown']], [93, 0, 93]) and
         old['donor_eligible'] is False and old['indirect_reference_completeness_claimed'] is False,
         '旧93unknownの厳密counter/候補/安全claim')
    need(type(old['rows']) is list and len(old['rows']) == 93 and
         all(type(row) is dict and set(row) == {'hit', 'owners'} and
             type(row['hit']) is dict and exact(row['owners'], []) for row in old['rows']),
         '旧93行の閉schemaとowner外を保持')
    rows = [row for row in old['rows'] if row['hit']['address'] != field.HIT]
    need(len(rows) == 92, '唯一の新4byte型だけをunknownから除く')
    need(exact([full['classified'], full['unclassified']], [782, 92]) and
         exact([row['hit'] for row in rows], [hit for hit in full['hits'] if hit['accepted'] is False]),
         '正式deltaの全92unknownと旧行の全field/順序が一致')
    result = copy.deepcopy(old)
    result.update(total=92, owner_unknown=0, unowned_unknown=92, rows=copy.deepcopy(rows))
    return result


def _successful_metadata(receipt):
    job = dict(id=JOB, name='minigame-text', status='completed', conclusion='success',
               run_id=RUN, logs_url=None, steps=[
                   dict(name=name, status='completed', conclusion='success', number=number)
                   for name, number in zip(STEP_NAMES, STEP_NUMBERS)])
    need(exact(receipt['job'], job), '同source jobと全10stepの成功終端/順序/型')
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
    for key, value in dict(status='ACCEPTED_ONE_JP_MINIGAME_MINIMUM_TYPE', source_head=HEAD,
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
    need(len(chain.PARENT_INPUTS) == 55 and len(validation.SOURCE_CODE) == 14,
         '全55保存親原本と閉14source境界')
    parent = chain.parent(*[(root / path).read_bytes() for path in chain.PARENT_INPUTS])
    need(exact([parent['classified'], parent['unclassified']], [781, 93]) and
         len(chain.INHERITED_NAMES) == 28 and
         sum(len(parent[name]['changes']) for name in chain.INHERITED_NAMES) == 162 and
         sum(len(parent[name]['witnesses']) for name in chain.INHERITED_NAMES) == 152,
         '正式781/93親と全28段162変更152witnessを保持')
    source_bindings = {path: identity((root / path).read_bytes()) for path in sorted(validation.SOURCE_CODE)}
    values = {name: validation.read_text(raw) for name, raw in files.items()}
    report = values['measurement.json']
    validation.validate_report(report, files['reference-chain.json'], parent, source_head=HEAD,
                               run_id=RUN, expected_bindings=source_bindings, test_count=152)
    need(exact(values['tests.json'], validation.test_summary(152)), '新152成功原本継承/旧suite再走0')
    need(exact(values['provenance.json'], validation.provenance(report)),
         '現在実測と独立疎fixtureを厳密に分離')
    delta = chain.read_measured(files['reference-chain.json'], FILES['reference-chain.json'], parent)
    full = chain.materialize(parent, delta)
    old_raw = (root / OLD_FRONTIER).read_bytes()
    checkpoint = validation.read_text((root / chain.PARENT_CHECKPOINT).read_bytes())
    need(exact(identity(old_raw), checkpoint['unknown_identity']), '親checkpointが束縛する旧93unknown原本')
    expected_frontier = unknown_frontier(full, validation.read_text(old_raw))
    need(exact(frontier, expected_frontier), '旧残92行の削除/改作/再順序/安全昇格を拒否')
    need(exact(receipt['unknown_identity'], identity(chain.canonical(frontier))), '残92unknownの完全identity')
    need(len(parent['hits']) == len(full['hits']) == 874 and
         all(exact(old, new) for old, new in zip(parent['hits'], full['hits']) if old['address'] != field.HIT),
         '他873行の全fieldと順序を保持')
    need(all(exact(full[key], value) for key, value in parent.items()
             if key not in {'hits', 'classified', 'unclassified', 'classifications'}),
         '全既受入namespace/source binding/安全claimを保持')
    return dict(status='PASS_RETAINED_782_CLASSIFIED_92_UNKNOWN', classified=782, unclassified=92,
                newly_classified=1, native_processes=0, measurement_replays=0,
                old_scope_test_reruns=0, donor_safe_bytes=0)


def main():
    _pins_ready()
    receipt = validation.read_text((ROOT / CP).read_bytes())
    files = {name: (ROOT / EVIDENCE / name).read_bytes() for name in FILES}
    frontier = validation.read_text((ROOT / FRONTIER).read_bytes())
    print(json.dumps(validate(receipt, files, frontier), sort_keys=True))


if __name__ == '__main__':
    main()
