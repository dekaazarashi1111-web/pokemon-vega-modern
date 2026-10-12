#!/usr/bin/env python3
"""新Blastoise成功4原本の診断receipt。正式783/91を変えず再測定しない。"""
from __future__ import annotations

import copy
import io
import json
import re
import stat
import zipfile
from pathlib import Path

import pr16_dex_hof_blastoise_validation as validation
import pr16_dex_hof_blastoise_chain as chain
import pr16_dex_hof_blastoise_asset as field

ROOT = Path(__file__).resolve().parents[1]
CP = 'content/modernization/pr16_dex_hof_blastoise_checkpoint.json'
EVIDENCE = 'content/modernization/pr16_dex_hof_blastoise_evidence'
FRONTIER = 'content/modernization/pr16_dex_hof_diploma_evidence/unknown-frontier.json'
GUIDE = 'docs/PR16_DEX_HOF_BLASTOISE_DIAGNOSTIC_JA.md'
HEAD = 'f9551f5d345949866a5dedd070da7479299922cd'
RUN = 37722012087
JOB = 113131584284
ARTIFACT_NAME = 'pr16-blastoise-asset-only'
# 成功artifact実取得と全9step/12loghashを照合した固定identity。
FILES = {'measurement.json': {'sha256': '65fe0fd1dab9ae3ee375228ad85884e51a5215f8827e4131edfd8adafc50f3e7',
                      'size': 25968},
 'provenance.json': {'sha256': 'd413a70ff25e6ce45f61be26e5a087dbf22920b1f0e90abb71a9b996ac7a8f5f',
                     'size': 14357},
 'reference-chain.json': {'sha256': 'dcef706ce658675552bd36fbb203b3409daa6eee72b4df94b647decf4ad0a31e',
                          'size': 1320},
 'tests.json': {'sha256': '14d8c76f2e5a5c56d19132bee13a3538d116b3740f093709256542d4b9e359b4',
                'size': 143}}
ARTIFACT_ID = 11525439041
ZIP_SIZE = 12207
ZIP_SHA = 'd364b3a4a324686421f19afbc370d0469cae7c8bf63a9915dee545d1829c28ec'
ARTIFACT_TIMES = {'created_at': '2026-10-08T03:20:16Z',
 'expires_at': '2027-01-06T03:17:23Z',
 'updated_at': '2026-10-08T03:20:16Z'}
JOB_LOG_ID = {'sha256': 'fa4f25ca2b65f78cea1803cbc791145d809933930583a75d83aae3b7b30a9dfd', 'size': 28092}
CURRENT_PROOF_ID = {'sha256': '12a331a1b2d640da0641f3aefdfe93e2b8d2ca6e62895ea0edd39335ebb18f90', 'size': 9742}
need, identity, exact = field.need, field.identity, validation.exact
COUNTERS = dict(
    schema_version=1, classified=783, unclassified=91, newly_classified=0,
    inherited_classified=783, inherited_unclassified=91, unit_tests=184,
    old_scope_test_reruns=0, current_rom_reconstructions=1, current_owner_count=115,
    saved_hit_count=874, current_saved_hits_rebound=874, inherited_parent_inputs=62,
    inherited_namespaces=30, inherited_changes=164, inherited_witnesses=154,
    source_file_count=14, public_source_file_count=14, accepted_namespaces=30,
    accepted_changes=164, accepted_witnesses=154, diagnostic_namespaces=1,
    materialized_namespaces=31, native_processes=0, donor_safe_bytes=0,
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
    'guide', 'previous_checkpoint', 'unknown_frontier', 'next_ja', *LOG_FIELDS})
STEP_NAMES = [
    'Set up job', 'Run actions/checkout@v4',
    'First scope across all branches and closed source boundary',
    'Official Ubuntu compiler for current candidate',
    'New Blastoise endpoint diagnostic and actual consumer only',
    'Closed successful text publication guard', 'Run actions/upload-artifact@v4',
    'Post Run actions/checkout@v4', 'Complete job']
STEP_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 14, 15]


def _pins_ready():
    need(type(FILES) is dict and set(FILES) == validation.FILES and
         all(validation.valid_identity(value) for value in FILES.values()) and
         type(ARTIFACT_ID) is int and ARTIFACT_ID > 0 and
         type(ZIP_SIZE) is int and ZIP_SIZE > 0 and type(ZIP_SHA) is str and
         re.fullmatch(r'[0-9a-f]{64}', ZIP_SHA) is not None and
         validation.valid_identity(JOB_LOG_ID) and validation.valid_identity(CURRENT_PROOF_ID) and
         type(ARTIFACT_TIMES) is dict and
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
    statuses = {'GENERATED_BLASTOISE_FILE_IDENTITY', 'PASS_BLASTOISE_PUBLIC_FILE'}
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
                for status in ('GENERATED_BLASTOISE_FILE_IDENTITY',
                               'PASS_BLASTOISE_PUBLIC_FILE', 'PASS_BLASTOISE_PUBLIC_FILE')
                for name in sorted(FILES)]
    need(exact(records, expected), '生成/検証/公開前の順序と各4fileを過不足なく保持')
    return dict(job_log_identity=copy.deepcopy(JOB_LOG_ID),
                **{key: copy.deepcopy(FILES) for key in LOG_FIELDS})


def unknown_frontier(full, old):
    """旧91unknownの全行・全field・順序をそのまま保持し、複製原本を作らない。"""
    need(type(old) is dict and set(old) == {
        'candidate', 'total', 'owner_unknown', 'unowned_unknown', 'rows',
        'donor_eligible', 'indirect_reference_completeness_claimed'}, '旧frontierの閉schema')
    need(exact(old['candidate'], field.CANDIDATE) and exact(full['candidate'], field.CANDIDATE) and
         exact([old['total'], old['owner_unknown'], old['unowned_unknown']], [91, 0, 91]) and
         old['donor_eligible'] is False and old['indirect_reference_completeness_claimed'] is False,
         '旧91unknownの厳密counter/候補/安全claim')
    need(type(old['rows']) is list and len(old['rows']) == 91 and
         all(type(row) is dict and set(row) == {'hit', 'owners'} and
             type(row['hit']) is dict and exact(row['owners'], []) for row in old['rows']),
         '旧91行の閉schemaとowner外を保持')
    need(exact([full['classified'], full['unclassified']], [783, 91]) and
         exact([row['hit'] for row in old['rows']],
               [hit for hit in full['hits'] if hit['accepted'] is False]),
         '診断後も対象083D6B61を含む全91unknownの全field/順序を保持')
    return copy.deepcopy(old)


def _successful_metadata(receipt):
    job = dict(id=JOB, name='blastoise-asset', status='completed', conclusion='success',
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
    for key, value in dict(status='DIAGNOSTIC_BLASTOISE_ENDPOINT_NO_NEW_TYPE', source_head=HEAD,
                           run_id=RUN, run_attempt=1, conclusion='success', candidate=field.CANDIDATE,
                           guide=GUIDE, previous_checkpoint=chain.PARENT_CHECKPOINT,
                           unknown_frontier=FRONTIER).items():
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
    need(len(chain.PARENT_INPUTS) == 62 and len(validation.SOURCE_CODE) == 14 and
         len(validation.sources.SOURCE_IDS) == 14,
         '全62保存親原本と閉14内部source/14公開source境界')
    parent = chain.parent(*[(root / path).read_bytes() for path in chain.PARENT_INPUTS])
    need(exact([parent['classified'], parent['unclassified']], [783, 91]) and
         len(chain.INHERITED_NAMES) == 30 and
         sum(len(parent[name]['changes']) for name in chain.INHERITED_NAMES) == 164 and
         sum(len(parent[name]['witnesses']) for name in chain.INHERITED_NAMES) == 154,
         '正式783/91親と全30段164変更154witnessを保持')
    source_bindings = {path: identity((root / path).read_bytes()) for path in sorted(validation.SOURCE_CODE)}
    values = {name: validation.read_text(raw) for name, raw in files.items()}
    report = values['measurement.json']
    validation.validate_report(report, files['reference-chain.json'], parent, source_head=HEAD,
                               run_id=RUN, expected_bindings=source_bindings, test_count=184)
    need(exact(values['tests.json'], validation.test_summary(184)), '新184成功原本継承/旧suite再走0')
    need(exact(values['provenance.json'], validation.provenance(report)),
         '現在実測と独立疎fixtureを厳密に分離')
    need(exact(identity(chain.canonical(report['scope_proof'])), CURRENT_PROOF_ID),
         '今回0641実取得proofの完全identity。開発fixtureの陽性/陰性への差替えを拒否')
    delta = chain.read_measured(files['reference-chain.json'], FILES['reference-chain.json'], parent)
    need(exact(delta['proof'], chain.zero_proof_template()) and
         exact(delta['changes'], []) and exact(delta['witnesses'], []) and
         exact([delta['newly_classified'], delta['classified'], delta['unclassified']], [0, 783, 91]),
         '診断namespaceは閉0件proof。陽性・近傍size・未消費tailを型へ昇格しない')
    full = chain.materialize(parent, delta)
    names = (*chain.INHERITED_NAMES, chain.NAMESPACE)
    need(set(full) == set(parent) | {chain.NAMESPACE} and
         exact(full[chain.NAMESPACE], delta) and len(names) == 31 and
         sum(len(full[name]['changes']) for name in names) == 164 and
         sum(len(full[name]['witnesses']) for name in names) == 154,
         '新31番目は診断0件namespaceのみ。正式30段164変更154witness保持')
    old_raw = (root / FRONTIER).read_bytes()
    checkpoint = validation.read_text((root / chain.PARENT_CHECKPOINT).read_bytes())
    need(exact(identity(old_raw), checkpoint['unknown_identity']), '親checkpointが束縛する旧91unknown原本')
    expected_frontier = unknown_frontier(full, validation.read_text(old_raw))
    need(exact(frontier, expected_frontier), '旧残91行の削除/改作/再順序/安全昇格を拒否')
    need(exact(receipt['unknown_identity'], identity(old_raw)) and
         exact(receipt['unknown_identity'], identity(chain.canonical(frontier))), '残91unknownの完全identity')
    need(len(parent['hits']) == len(full['hits']) == 874 and
         all(exact(old, new) for old, new in zip(parent['hits'], full['hits'])),
         '対象4byteを含む全874行の全fieldと順序を保持')
    need(all(exact(full[key], value) for key, value in parent.items()),
         '全既受入namespace/source binding/安全claimを保持')
    return dict(status='PASS_BLASTOISE_DIAGNOSTIC_RETAINED_783_CLASSIFIED_91_UNKNOWN', classified=783, unclassified=91,
                newly_classified=0, native_processes=0, measurement_replays=0,
                old_scope_test_reruns=0, donor_safe_bytes=0)


def main():
    _pins_ready()
    receipt = validation.read_text(validation.read_regular(ROOT / CP))
    directory = ROOT / EVIDENCE
    need({path.name for path in directory.iterdir()} == set(FILES),
         '診断保存directoryは新4原本だけ。unknown複製/余剰raw/bytehexを拒否')
    files = {name: validation.read_regular(directory / name) for name in FILES}
    frontier = validation.read_text(validation.read_regular(ROOT / FRONTIER))
    print(json.dumps(validate(receipt, files, frontier), sort_keys=True))


if __name__ == '__main__':
    main()
