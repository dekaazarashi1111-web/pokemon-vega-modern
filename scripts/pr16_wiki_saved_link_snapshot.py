#!/usr/bin/env python3
"""成功済み保存ELF読取artifactを一度だけ固定する。再取得後はtracked textのみ。"""
from __future__ import annotations
import io
import os
import urllib.request
import zipfile
from pr16_candidate_wiki_inputs import Inputs, ROOT, digest, need, stable, strict
from pr16_wiki_followup_sources import RedirectWithoutCredential

OUTPUT = 'content/modernization/pr16_candidate_wiki_saved_link_sources.json'
ARTIFACT = 10624750708
ARCHIVE_SHA = '7169bb41d334d783ff860dd7df2565958ce7fc8d525aca23896f0c305213e198'
REPORT_SHA = '60d57ca066646e46e82594cd7404ae7bfd5041af7451e2cdc40d612c18045a77'
SNAPSHOT_SHA = '8a85f18fa4f4e7d82704c4f29e327d3c0e8d8c09f3ddc03fc46df5ce67b6ccaf'


def compact(raw: bytes) -> dict:
    need(digest(raw) == REPORT_SHA, '保存ELF report hash不一致')
    value = strict(raw)
    need(value['run_id'] == 35567438143 and value['source_head'] == '04118e975badc0cc344d06451a37c8a7720ebe18', '保存ELF run/head不一致')
    result = {k: value[k] for k in ('schema_version', 'source_head', 'run_id', 'candidate', 'metadata',
        'archives', 'elf', 'cache_index', 'symbols', 'direct_callees', 'move_rows', 'summary',
        'new_native_runs', 'arm_builds', 'rom_changes', 'saved_byte_restoration_only',
        'runtime_reachability_proven', 'all_indirect_edges_resolved')}
    result['graphs'] = {name: {k:v for k,v in graph.items() if k != 'nodes'} for name,graph in value['graphs'].items()}
    result['capture_receipt'] = {'run':35567438143, 'conclusion':'success', 'job':106231970424,
        'artifact_id':ARTIFACT, 'artifact_sha256':ARCHIVE_SHA, 'report_sha256':REPORT_SHA,
        'unit_tests':40, 'failed_predecessor':35566920479,
        'failure_ja':'保存ELFのsymbol表読取上限で停止。大規模有界表と切詰め拒否2試験を追加し修正。',
        'source_body_equivalence_not_claimed':True}
    return result


def load(inputs: Inputs) -> dict:
    raw = inputs.raw(OUTPUT)
    need(digest(raw) == SNAPSHOT_SHA, '保存ELF text snapshot hash不一致')
    return strict(raw)


def main() -> None:
    if (ROOT/OUTPUT).exists():
        load(Inputs()); print('PASS_EXISTING_SAVED_LINK_SNAPSHOT_NO_NETWORK'); return
    token = os.environ.get('GITHUB_TOKEN'); need(token, '初回artifact取得tokenなし')
    request = urllib.request.Request(
        f'https://api.github.com/repos/dekaazarashi1111-web/pokemon-vega-modern/actions/artifacts/{ARTIFACT}/zip',
        headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
    opener = urllib.request.build_opener(RedirectWithoutCredential())
    with opener.open(request, timeout=60) as response:
        raw = response.read(1_000_001)
    need(len(raw) <= 1_000_000 and digest(raw) == ARCHIVE_SHA, '保存ELF artifact digest/size不一致')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        need(len(archive.namelist()) == len(set(archive.namelist())), 'artifact member重複')
        need(archive.getinfo('report.json').file_size <= 1_000_000, 'report size超過')
        result = stable(compact(archive.read('report.json')))
    need(digest(result) == SNAPSHOT_SHA, '保存ELF snapshot生成不一致')
    (ROOT/OUTPUT).write_bytes(result)
    print('PASS_FIXED_SAVED_LINK_SNAPSHOT_NATIVE_0_ARM_0')

if __name__ == '__main__': main()
