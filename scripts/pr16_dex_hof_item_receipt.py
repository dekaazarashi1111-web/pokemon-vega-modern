#!/usr/bin/env python3
"""回復runの保存4原本と成功終端だけを受け入れる。ROM/reader/旧suiteは再走しない。"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pr16_dex_hof_item_recovery_validation as validation
import pr16_dex_hof_jp_item_chain as chain
import pr16_dex_hof_jp_item_text as field

ROOT = Path(__file__).resolve().parents[1]
CP = 'content/modernization/pr16_dex_hof_jp_item_checkpoint.json'
EVIDENCE = 'content/modernization/pr16_dex_hof_jp_item_evidence'
FRONTIER = EVIDENCE + '/unknown-frontier.json'
OLD_FRONTIER = 'content/modernization/pr16_dex_hof_jp_field_evidence/unknown-frontier.json'
GUIDE = 'docs/PR16_DEX_HOF_ITEM_ACCEPTED_JA.md'
HEAD = 'd7543f17a4de18c731de42e12d3608832555e1da'
RUN = 37704409163
JOB = 113075243551
ARTIFACT_NAME = 'pr16-jp-item-recovery-text-only'
# 成功artifactの実取得と生成/公開前logの一致確認後に凍結した完全byte identity。
FILES = {
    'measurement.json': {'size': 772253, 'sha256': '38a63b8ae95597f9c6b428c4fb88199141ff5743774303617d873212e4115255'},
    'provenance.json': {'size': 2921, 'sha256': 'f7db3f439d4a41d157951b858a81e337bd32b6319bc31f2ba2cbb4b722b395d6'},
    'reference-chain.json': {'size': 351398, 'sha256': '5756495e9af69dba2f3d59334a33cf93358de233dd93406dddeaf44e7be85f32'},
    'tests.json': {'size': 189, 'sha256': 'ce9166c9b8c17e6456b955fbd6dcae894514294dd68f1cb0b5f58dde1600ea32'},
}
ARTIFACT_ID = 11518044429
ZIP_SIZE = 120441
ZIP_SHA = '82822cf4a8f5baea0ab8cea42c5bd4c35af54a0bba58580d2009d5340945bbfd'
INHERITED_LOG_ID = {'size': 24250, 'sha256': '6b0e5f7bb670ece6c2753bd2e26ce3b1c069f3b5b6187c3737135e3be050f70c'}
PRIOR_RECOVERY_LOG_ID = {'size': 25706, 'sha256': '0cec21b4731020920bfc12fd96a9043a837d754a5b8e575ed590d2257f8fea0c'}
need, identity, exact = field.need, field.identity, validation.exact
COUNTERS = dict(
    schema_version=1, classified=781, unclassified=93, newly_classified=1,
    inherited_classified=780, inherited_unclassified=94,
    inherited_scope_tests=165, recovery_test_count=27, old_scope_test_reruns=0,
    current_rom_reconstructions=1, cumulative_scope_rom_reconstructions=3,
    consumer_remeasurements=2, current_owner_count=115, native_processes=0,
    donor_safe_bytes=0, old_full_rom_scan_runs=0, old_native_cases_replayed=0,
    formal_rom_changed=False, formal_save_changed=False, donor_eligible=False,
    donor_leased=False, original_failed_run_rewritten=False,
    reconstructed_text_promoted_as_original=False, all_prior_accepted_retained=True,
    remaining_unknown_rows_retained=True)
RECEIPT_FIELDS = frozenset(COUNTERS) | frozenset({
    'status', 'source_head', 'run_id', 'run_attempt', 'conclusion', 'job', 'artifact',
    'candidate', 'evidence_bindings', 'delta_identity', 'measurement_identity',
    'tests_identity', 'provenance_identity', 'unknown_identity', 'original_failed_run', 'prior_failed_recovery',
    'guide', 'previous_checkpoint', 'next_ja'})
STEP_NAMES = [
    'Set up job', 'Run actions/checkout@v4', 'Same branch and closed source boundary',
    'Official Ubuntu compiler for current candidate',
    'Recover two current readers without rerunning 165 inherited tests',
    'Closed successful text publication guard', 'Run actions/upload-artifact@v4',
    'Read-only checkout and task graph', 'Post Run actions/checkout@v4', 'Complete job']
STEP_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 8, 16, 17]


def _pins_ready():
    need(type(FILES) is dict and set(FILES) == validation.FILES and
         all(validation._valid_identity(value) for value in FILES.values()) and
         type(ARTIFACT_ID) is int and ARTIFACT_ID > 0 and
         type(ZIP_SIZE) is int and ZIP_SIZE > 0 and type(ZIP_SHA) is str and
         re.fullmatch(r'[0-9a-f]{64}', ZIP_SHA) is not None and
         validation._valid_identity(INHERITED_LOG_ID) and
         validation._valid_identity(PRIOR_RECOVERY_LOG_ID),
         '成功4原本/取得ZIP/元failure2本のjob logの実取得identity確定前は受入不可')


def unknown_frontier(full, old):
    """旧94行から083DE02Bだけを除き、他93行の全fieldと順序を保存する。"""
    need(type(old) is dict and set(old) == {
        'candidate', 'total', 'owner_unknown', 'unowned_unknown', 'rows',
        'donor_eligible', 'indirect_reference_completeness_claimed'}, '旧frontierの閉schema')
    need(exact(old['candidate'], field.CANDIDATE) and
         exact(full['candidate'], field.CANDIDATE) and
         exact([old['total'], old['owner_unknown'], old['unowned_unknown']], [94, 0, 94]) and
         old['donor_eligible'] is False and old['indirect_reference_completeness_claimed'] is False,
         '旧94unknownの厳密counter/候補/安全claim')
    need(type(old['rows']) is list and len(old['rows']) == 94 and
         all(type(row) is dict and set(row) == {'hit', 'owners'} and
             type(row['hit']) is dict and row['owners'] == [] for row in old['rows']),
         '旧94行の閉schemaとowner外を保持')
    rows = [row for row in old['rows'] if row['hit']['address'] != field.HIT]
    need(len(rows) == 93, '唯一の新4byte型だけをunknownから除く')
    need(exact([full['classified'], full['unclassified']], [781, 93]) and
         exact([row['hit'] for row in rows], [hit for hit in full['hits'] if hit['accepted'] is False]),
         '正式deltaの全93unknownと旧行の全field/順序が一致')
    result = copy.deepcopy(old)
    result.update(total=93, owner_unknown=0, unowned_unknown=93, rows=copy.deepcopy(rows))
    return result


def _successful_metadata(receipt):
    job = dict(id=JOB, name='item-recovery', status='completed', conclusion='success',
               run_id=RUN, logs_url=None, steps=[
                   dict(name=name, status='completed', conclusion='success', number=number)
                   for name, number in zip(STEP_NAMES, STEP_NUMBERS)])
    need(exact(receipt['job'], job), '同source回復jobと全10stepの成功終端/順序/型')
    artifact = receipt['artifact']
    need(type(artifact) is dict and set(artifact) == {
        'id', 'name', 'size_in_bytes', 'url', 'archive_download_url', 'expired',
        'created_at', 'expires_at', 'updated_at', 'digest', 'workflow_run'},
        '取得artifactの閉schema')
    url = ('https://api.github.com/repos/dekaazarashi1111-web/pokemon-vega-modern/'
           'actions/artifacts/' + str(ARTIFACT_ID))
    expected = dict(id=ARTIFACT_ID, name=ARTIFACT_NAME, size_in_bytes=ZIP_SIZE,
                    url=url, archive_download_url=url + '/zip', expired=False,
                    digest='sha256:' + ZIP_SHA, workflow_run=dict(
                        id=RUN, repository_id=1358127462, head_repository_id=1358127462,
                        head_branch='codex/modernization-followup-20260908', head_sha=HEAD))
    need(all(exact(artifact[key], value) for key, value in expected.items()),
         '外側ZIP完全identityと同repository/branch/run/sourceの厳密型')
    need(all(type(artifact[key]) is str and re.fullmatch(
        r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', artifact[key]) is not None
        for key in ('created_at', 'expires_at', 'updated_at')), '取得時artifact時刻の閉形式')


def validate(receipt, files, frontier, root=ROOT):
    """外部取得も測定もせず、保存済み原本・source・receipt・frontierを照合する。"""
    _pins_ready()
    need(type(files) is dict and set(files) == set(FILES), '成功artifactの閉4fileだけ')
    need(all(type(files[name]) is bytes and exact(identity(files[name]), expected)
             for name, expected in FILES.items()), '成功4原本の完全byte identity')
    need(type(receipt) is dict and set(receipt) == RECEIPT_FIELDS, '閉じた受入receipt schema')
    for key, value in COUNTERS.items():
        need(exact(receipt[key], value), '厳密な受入counter/flag: ' + key)
    for key, value in dict(status='ACCEPTED_ONE_JP_ITEM_MINIMUM_TYPE_RECOVERY', source_head=HEAD,
                           run_id=RUN, run_attempt=1, conclusion='success', candidate=field.CANDIDATE,
                           guide=GUIDE, previous_checkpoint=chain.PARENT_CHECKPOINT).items():
        need(exact(receipt[key], value), '回復成功identity/guide/親checkpoint: ' + key)
    need(type(receipt['next_ja']) is str and bool(receipt['next_ja'].strip()), '次工程の明記')
    _successful_metadata(receipt)
    need(exact(receipt['evidence_bindings'], {EVIDENCE + '/' + name: value
                                            for name, value in FILES.items()}), '保存4原本の参照binding')
    for key, name in (('delta_identity', 'reference-chain.json'), ('measurement_identity', 'measurement.json'),
                      ('tests_identity', 'tests.json'), ('provenance_identity', 'provenance.json')):
        need(exact(receipt[key], FILES[name]), '保存原本の完全identity: ' + key)
    root = Path(root)
    parent = chain.parent(*[(root / path).read_bytes() for path in chain.PARENT_INPUTS])
    source_bindings = {path: identity((root / path).read_bytes()) for path in sorted(validation.SOURCE_CODE)}
    values = {name: validation.read_text(raw) for name, raw in files.items()}
    report = values['measurement.json']
    validation.validate_report(report, files['reference-chain.json'], parent, source_head=HEAD,
                               run_id=RUN, expected_bindings=source_bindings, recovery_test_count=27)
    need(exact(values['tests.json'], validation.test_summary(27)), '旧165継承/新27成功/旧suite再走0')
    provenance = validation.provenance(report, inherited_log_identity=INHERITED_LOG_ID,
                                       prior_recovery_log_identity=PRIOR_RECOVERY_LOG_ID)
    need(exact(values['provenance.json'], provenance),
         '元failure/失われたhashなし/参考fixture/今回新原本の厳密な分離')
    need(exact(receipt['original_failed_run'], provenance['original_failed_run']),
         '元測定step成功でもrun全体failure/artifact0をreceiptに保持')
    need(exact(receipt['prior_failed_recovery'], provenance['prior_failed_recovery']),
         '第1回復の型検査failure/測定成功claimなし/原本なしもreceiptに保持')
    delta = chain.read_measured(files['reference-chain.json'], FILES['reference-chain.json'], parent)
    full = chain.materialize(parent, delta)
    old_raw = (root / OLD_FRONTIER).read_bytes()
    checkpoint = validation.read_text((root / chain.PARENT_CHECKPOINT).read_bytes())
    need(exact(identity(old_raw), checkpoint['unknown_identity']), '親checkpointが束縛する旧94unknown原本')
    expected_frontier = unknown_frontier(full, validation.read_text(old_raw))
    need(exact(frontier, expected_frontier), '旧残93行の削除/改作/再順序/安全昇格を拒否')
    need(exact(receipt['unknown_identity'], identity(chain.canonical(frontier))), '残93unknownの完全identity')
    need(len(parent['hits']) == len(full['hits']) == 874 and
         all(exact(old, new) for old, new in zip(parent['hits'], full['hits']) if old['address'] != field.HIT),
         '他873行の全fieldと順序を保持')
    need(all(exact(full[key], value) for key, value in parent.items()
             if key not in {'hits', 'classified', 'unclassified', 'classifications'}),
         '全既受入namespace/source binding/安全claimを保持')
    return dict(status='PASS_RETAINED_781_CLASSIFIED_93_UNKNOWN', classified=781, unclassified=93,
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
