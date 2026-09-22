#!/usr/bin/env python3
"""失敗nativeハーネス限定の回復。成功済みhost試験は同じ証拠を再利用する。"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT),str(ROOT/'scripts')]
import pr16_learnset_runtime_verify as v
from pr16_wiki_reconcile import fetch
from tools import pr16_learnset_successor as s
from pr16_learnset_floette_verify import download

REQUEST = '.github/pr16-learnset-runtime-run.json'


def main():
    request = s.read_json(ROOT/REQUEST)
    v.need(request['mode']=='native-harness-recovery' and request['task']==v.linker.TASK,'回復scope不一致')
    run = fetch(f"actions/runs/{request['previous_run']}")
    v.need(run['head_sha']==request['previous_head'] and run['conclusion']=='failure'
           and run['status']=='completed' and run['path']=='.github/workflows/pr16-learnset-runtime.yml', '先行失敗run不一致')
    # Runtime C/packing/host oracle/test本文は旧HEADと完全一致を要求する。
    excluded = {'tools/mgba_pr16_learnset_runtime.c','.github/workflows/pr16-learnset-runtime.yml'}
    for name in set(v.CODE)-excluded:
        original = subprocess.check_output(['git','show',request['previous_head']+':'+name],cwd=ROOT)
        v.need(original==(ROOT/name).read_bytes(), 'host証拠再利用に影響する変更: '+name)
    previous = v.WORK/'prior-proof'
    download(request['proof_artifact'],request['previous_head'],previous,request['members'])
    unit = (previous/'unit.txt').read_text(); host = s.read_json(previous/'host-audit.json')
    v.need(re.findall(r'^Ran (\d+) tests? in ',unit,re.M)==['19'] and re.search(r'\nOK\s*$',unit)
           and host['status']=='PASS_PLACED_C_AGAINST_ACCEPTED_SPANS','先行host成功原本不一致')
    v.CODE += (REQUEST,'scripts/pr16_learnset_runtime_recovery.py')
    execute, samples = v.execute, v.samples
    def recovered_execute(args,log,*,env=None):
        if log.name=='unit.txt':
            log.write_text(unit)
            return b''
        if log.name=='native-compile.txt':
            args = [*args[:1],'-g','-rdynamic','-fsanitize=address,undefined',*args[1:]]
        if log.name.startswith('native'):
            env = dict(os.environ,ASAN_OPTIONS='detect_leaks=0:abort_on_error=1')
        return execute(args,log,env=env)
    def recovered_audit(folder,expected):
        v.need(s.identity(folder/'runtime-image.bin')==v.EXPECTED_IMAGE and len(expected)==host['owners'], '再利用image不一致')
        return host
    def checkpoint_samples(folder,expected,report):
        selected = samples(folder,expected,report)
        out = v.WORK/'link-checkpoint'; out.mkdir()
        for name in ('runtime-image.bin','runtime-bundle.bin','receipt.json','link.json','disassembly.txt','pr16_learnset_samples.h'):
            shutil.copyfile(folder/name,out/name)
        (out/'entrypoints.jsonl').write_bytes(b''.join(s.encode(row) for row in expected))
        (out/'checkpoint.json').write_bytes(s.encode({'status':'ARM_AND_HOST_PASS_NATIVE_PENDING',
            'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
            'candidate':report['candidate'],'files':v.identities(out),
            'code_bindings':{name:s.identity(ROOT/name) for name in v.CODE},
            'host_reused_from':request['previous_run'],'gameplay_e2e':False}))
        (v.WORK/'proof'/'reuse.json').write_bytes(s.encode({'prior_run':request['previous_run'],
            'prior_head':request['previous_head'],'artifact':request['proof_artifact'],
            'unit_tests_reexecuted':0,'host_queries_reexecuted':0,'runtime_c_unchanged':True,
            'new_arm_rebuild_reason':'prior failed run did not retain bundle; new pre-native checkpoint prevents recurrence'}))
        return selected
    v.execute = recovered_execute; v.audit = recovered_audit; v.samples = checkpoint_samples
    v.verify()


if __name__=='__main__':
    main()
