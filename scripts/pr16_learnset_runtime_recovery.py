#!/usr/bin/env python3
"""成功したhost/独立ARM配置を再利用し、修正したnative終了処理だけを検証。"""
from __future__ import annotations
import os
from pathlib import Path
import re
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_learnset_runtime_verify as v
from pr16_wiki_reconcile import fetch
from tools import pr16_learnset_successor as s
from pr16_learnset_floette_verify import download

REQUEST='.github/pr16-learnset-runtime-run.json'


def restore_candidate(folder,source):
    """保存bundleの復元のみ。compiler、旧native、payload生成器は呼ばない。"""
    v.need(not folder.exists(),'重複復元禁止');folder.mkdir()
    for name in ('runtime-image.bin','runtime-bundle.bin','receipt.json','link.json','disassembly.txt','pr16_learnset_samples.h'):
        shutil.copyfile(source/name,folder/name)
    report=s.read_json(folder/'link.json')
    parent=(v.WORK/'accepted-parent.gba').read_bytes()
    v.need(v.linker.saved.identity(parent)==v.linker.PARENT,'固定親identity違反')
    raw=bytearray(parent);bundle=(folder/'runtime-bundle.bin').read_bytes();start=report['start']
    v.need(v.linker.saved.identity(bundle)==report['bundle'] and parent[start:start+len(bundle)]==b'\xff'*len(bundle),'保存bundle/preimage違反')
    raw[start:start+len(bundle)]=bundle
    for patch in report['hooks']:
        at=patch['offset'];before=bytes.fromhex(patch['before']);after=bytes.fromhex(patch['after'])
        v.need(parent[at:at+len(before)]==before and len(before)==len(after)==8,'保存hook preimage違反')
        raw[at:at+8]=after
    v.need(v.linker.saved.identity(raw)==report['candidate'],'保存候補復元hash違反')
    (folder/'candidate.gba').write_bytes(raw)


def main():
    request=s.read_json(ROOT/REQUEST);fixed=request['link_checkpoint']
    v.need(request['mode']=='native-only-from-link-checkpoint' and request['task']==v.linker.TASK,'回復scope不一致')
    run=fetch(f"actions/runs/{fixed['run_id']}")
    v.need(run['head_sha']==fixed['source_head'] and run['conclusion']=='failure'
           and run['status']=='completed' and run['path']=='.github/workflows/pr16-learnset-runtime.yml','先行失敗run不一致')
    source=v.WORK/'link-checkpoint'
    download(fixed['artifact'],fixed['source_head'],source,fixed['members'])
    checkpoint=s.read_json(source/'checkpoint.json')
    v.need(checkpoint['source_head']==fixed['source_head'] and checkpoint['run_id']==fixed['run_id']
           and checkpoint['status']=='ARM_AND_HOST_PASS_NATIVE_PENDING'
           and checkpoint['host_reused_from']==request['previous_run'],'保存checkpoint scope不一致')
    for name,binding in checkpoint['files'].items():s.bound(source/name,binding)
    allowed={'tools/mgba_pr16_learnset_runtime.c','.github/workflows/pr16-learnset-runtime.yml',
             REQUEST,'scripts/pr16_learnset_runtime_recovery.py'}
    expected=set(v.CODE)|{REQUEST,'scripts/pr16_learnset_runtime_recovery.py'}
    v.need(set(checkpoint['code_bindings'])==expected,'保存code binding集合不一致')
    for name,binding in checkpoint['code_bindings'].items():
        if name not in allowed:s.bound(ROOT/name,binding)
    # 原host oracle/packing/runtime C/test本文のhashは前回と同一。
    previous=v.WORK/'prior-proof'
    download(request['proof_artifact'],request['previous_head'],previous,request['members'])
    unit=(previous/'unit.txt').read_text();host=s.read_json(previous/'host-audit.json')
    v.need(re.findall(r'^Ran (\d+) tests? in ',unit,re.M)==['19'] and re.search(r'\nOK\s*$',unit)
           and host['status']=='PASS_PLACED_C_AGAINST_ACCEPTED_SPANS','先行host成功原本不一致')
    v.CODE+=(REQUEST,'scripts/pr16_learnset_runtime_recovery.py')
    execute,samples=v.execute,v.samples
    def recovered_execute(args,log,*,env=None):
        if log.name=='unit.txt':
            log.write_text(unit);return b''
        if log.name in ('build11.txt','build29.txt'):
            restore_candidate(Path(args[-1]),source)
            log.write_bytes(s.encode({'status':'RESTORED_ACCEPTED_ARM_BYTES','source_run':fixed['run_id'],'arm_compiles':0,'arm_links':0}))
            return b''
        if log.name=='native-compile.txt':
            args=[*args[:1],'-g','-rdynamic','-fsanitize=address,undefined',*args[1:]]
        if log.name.startswith('native'):
            env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:abort_on_error=1')
        return execute(args,log,env=env)
    def recovered_audit(folder,expected):
        v.need(s.identity(folder/'runtime-image.bin')==v.EXPECTED_IMAGE and len(expected)==host['owners'],'再利用image不一致')
        return host
    def recovered_samples(folder,expected,report):
        selected=samples(folder,expected,report)
        v.need((folder/'pr16_learnset_samples.h').read_bytes()==(source/'pr16_learnset_samples.h').read_bytes(),'同じnative対象ではない')
        (v.WORK/'proof'/'reuse.json').write_bytes(s.encode({'prior_run':request['previous_run'],
            'prior_head':request['previous_head'],'artifact':request['proof_artifact'],
            'unit_tests_reexecuted':0,'host_queries_reexecuted':0,'runtime_c_unchanged':True,
            'link_reused_from':fixed,'arm_compiles_reexecuted':0,'arm_links_reexecuted':0,
            'native_repair':'remove free(core) after mGBA core->deinit owns and frees core',
            'prior_failed_native_runs':[35703376221,35703851133]}))
        return selected
    v.execute=recovered_execute;v.audit=recovered_audit;v.samples=recovered_samples
    v.verify()
    # 継承した独立生成証拠を今回の新規compile件数として数えない。
    path=v.WORK/'proof'/'verification.json';report=s.read_json(path)
    report.update(new_arm_compiles=0,new_arm_links=0,independent_processes=0,
                  inherited_arm_compiles=8,inherited_arm_links=2,inherited_independent_build_processes=2,
                  inherited_arm_evidence_run=fixed['run_id'],candidate_restore_copies=2,
                  focused_tests_executed=0,host_queries_executed=0,
                  prior_failed_native_processes=2,native_harness_sanitizers=['address','undefined'])
    path.write_bytes(s.encode(report))


if __name__=='__main__':main()
