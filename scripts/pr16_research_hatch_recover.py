#!/usr/bin/env python3
"""Recover only five saved PASS cases from an interrupted run. No emulation."""
from __future__ import annotations
import copy
import datetime
import json
import os
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_research_hatch_proof as p
SELF='scripts/pr16_research_hatch_recover.py'
TEST='tests/test_pr16_research_hatch_recover.py'
WF='.github/workflows/pr16-research-hatch-recover-20260925.yml'
CODE={SELF,TEST,WF,p.SELF,p.TEST}
SOURCE='e12eda4098837fcd434194e3da713f2837209450'
RUN=36138860612
CASES=tuple('research-egg-'+str(x) for x in (1201,1204,1206,1208,1210))
PROOF={'id':10868027070,'name':'pr16-research-hatch-proof','size_in_bytes':45208,'digest':'sha256:1b89c98fc132c65243dea0b0cccea415accadf90b389231e0fec32f5552f3f89'}
SCREENS={'id':10868426825,'name':'pr16-research-hatch-screens','size_in_bytes':26642,'digest':'sha256:77282fc6d2b47784a8191df2b083f57fac6aa97dc3052620ed7cc7a24116fe38'}
CANDIDATE={'size':33554432,'sha256':'b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91'}
BASE_NAMES={'compile.process.json','compile.stdout.txt','compile.stderr.txt','unit.process.json','unit.stdout.txt','unit.stderr.txt','fixture-sources.json','recipe.json','vectors.h','verification.json'}
NEXT='研究孵化の保存成功5件と32unitは再実行しない。残り10件を1case/workerの独立Actionsで並列測定し、集約jobだけが記録・非force pushする。50cycle/実歩数/既存C・候補ROMは変更しない。15件完了後に特殊野生へ。'


def project(original,names):
    """Preserve original evidence; derive a separate truthful partial checkpoint."""
    p.need(original['run_id']==RUN and original['source_head']==SOURCE,'interrupted origin')
    p.need(original['status']=='RUNNING' and original['candidate']==CANDIDATE,'interrupted candidate/status')
    p.need(set(original['accepted'])==set(CASES) and not original['failures'],'exact five successes')
    p.need(original['native_processes']==5 and original['host_compiles']==1 and original['new_unit_tests']==32,'saved counters')
    p.need(original['unit_passed'] is True and original['unit_origin']==RUN,'unit origin')
    for key in ('actions_completion_confirmed','issue19_complete','release_ready','active_baseline_changed'):
        p.need(original[key] is False,'scope '+key)
    for key in ('accepted_case_reruns','gift_reruns','arm_compiles','rom_changes','wiki_generations'):
        p.need(type(original[key]) is int and original[key]==0,'no rerun '+key)
    p.need(len(names)==15 and len(set(names))==15 and set(CASES)<=set(names),'complete case domain')
    value=copy.deepcopy(original)
    value.update(status='PARTIAL_RESEARCH_HATCH_RECOVERED_AFTER_TIMEOUT',pending_cases=[n for n in names if n not in CASES])
    return value


def execute():
    import pr16_research_hatch as r
    import pr16_natural_supply as s
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_wiki_actions import current
    from pr16_learnset_compact_record import publish_resume
    from common import redact_user_paths,user_absolute_path_lines
    head=current()
    p.need(not (ROOT/r.CP).exists(),'recover once; do not replace a newer checkpoint')
    run=fetch('actions/runs/'+str(RUN))
    p.need(run['head_sha']==SOURCE and run['status']=='completed' and run['conclusion']=='cancelled' and run['path']==r.WF,'cancelled source retained')
    jobs=fetch('actions/runs/'+str(RUN)+'/jobs?per_page=100')
    p.need(jobs['total_count']==len(jobs['jobs'])==1,'one original job')
    job=jobs['jobs'][0];steps={x['number']:x['conclusion'] for x in job['steps']}
    p.need(job['conclusion']=='cancelled' and steps[5]=='cancelled' and steps[6]==steps[7]==steps[9]==steps[10]=='success' and steps[8]=='skipped','saved evidence, push skipped')
    listing=fetch('actions/runs/'+str(RUN)+'/artifacts?per_page=100')
    p.need(listing['total_count']==len(listing['artifacts'])==2,'complete artifact inventory')
    proof_names=BASE_NAMES|{n+suffix for n in CASES for suffix in ('.process.json','.stdout.txt','.stderr.txt')}
    image_names={n+'-'+stage+'.ppm' for n in CASES for stage in ('hatched','continued')}
    def get(meta,names):
        matches=[a for a in listing['artifacts'] if a['name']==meta['name']]
        p.need(len(matches)==1 and all(matches[0][k]==v for k,v in meta.items()),'pinned artifact identity')
        raw=fetch('actions/artifacts/'+str(meta['id'])+'/zip',binary=True)
        return p.archive(raw,matches[0],dict.fromkeys(names),RUN,SOURCE)
    data=get(PROOF,proof_names);images=get(SCREENS,image_names)
    r.PROOF.mkdir(parents=True,exist_ok=True)
    (r.PROOF/'original-verification.json').write_bytes(data['verification.json'])
    original=r.load(r.PROOF/'original-verification.json');v=project(original,r.NAMES)
    p.need('proof_bindings' not in original and 'screenshots' not in original,'interrupted finally was not recorded')
    p.need(json.loads(data['unit.process.json'])==json.loads(data['compile.process.json'])==dict(returncode=0,timed_out=False),'unit and host processes')
    p.need(re.search(rb'Ran 32 tests in ',data['unit.stderr.txt']) and b'\nOK\n' in data['unit.stderr.txt'] and not data['compile.stderr.txt'],'32 saved unit / warning-free host')
    for name in CASES:
        a=v['accepted'][name]
        p.need(a['run_id']==RUN and a['source_head']==SOURCE and a['contract']==v['contracts'][name],'case origin/contract '+name)
        p.need(json.loads(data[name+'.process.json'])==dict(returncode=0,timed_out=False),'saved native process '+name)
        p.need(r.validate(data[name+'.stdout.txt'],data[name+'.stderr.txt'],a['contract']['fixture'])==a['result'],'saved raw case '+name)
    for path,binding in {**v['source_bindings'],**v['protected_bindings'],**v['compiled_sources']}.items():
        p.need(p.identity((ROOT/path).read_bytes())==binding,'original source/protected binding '+path)
    frames={name:p.frame(raw) for name,raw in images.items()}
    p.need(len(frames)==10 and all(x['nonblank'] for x in frames.values()),'10 rendered field-return frames')
    original_dir=ROOT/r.EVIDENCE/str(RUN)
    p.need(not original_dir.exists(),'do not overwrite original evidence');original_dir.mkdir(parents=True)
    for name,raw in data.items():
        text=raw.decode();p.need('\0' not in text,'text evidence only')
        safe='\n'.join(x.rstrip() for x in redact_user_paths(text).splitlines()).rstrip()+'\n' if text else ''
        p.need(not user_absolute_path_lines(safe),'no private path')
        (original_dir/name).write_text(safe)
    # These are explicitly reconstructed indexes, not invented original-finally output.
    v['proof_bindings']={name:p.identity(raw) for name,raw in data.items() if name!='verification.json'}
    v['screenshots']={name:p.identity(raw) for name,raw in images.items()}
    v['public_evidence_bindings']={f.name:p.identity(f.read_bytes()) for f in original_dir.iterdir()}
    v['evidence_path']=original_dir.relative_to(ROOT).as_posix()
    unit_err=(r.PROOF/'recovery-unit.stderr.txt').read_bytes();count=re.search(rb'Ran (\d+) tests? in ',unit_err)
    p.need(count and b'\nOK\n' in unit_err,'new recovery unit PASS')
    receipt=dict(schema_version=1,status='RECOVERED_FIVE_NATIVE_PASS_CASES_FROM_CANCELLED_RUN',
                 source_head=head,run_id=int(os.environ['GITHUB_RUN_ID']),original_run_id=RUN,original_source_head=SOURCE,
                 original_conclusion='cancelled',original_status='RUNNING',original_push_executed=False,
                 proof=PROOF,screens=SCREENS,original_verification=p.identity(data['verification.json']),frames=frames,
                 accepted_cases=list(CASES),pending_cases=v['pending_cases'],raw_revalidations=5,
                 new_native_processes=0,old_unit_tests=0,new_unit_tests=int(count[1]),host_compiles=0,arm_compiles=0,rom_changes=0,
                 original_post_loop_input_mtime_check_completed=False,unrecorded_inflight_attempt_not_ruled_out=True,
                 visual_review='10 field-return frames are nonblank and consistent; no Pokemon form/move UI is visible.',
                 pokemon_identity_visual_acceptance=False,all_fifteen_complete=False,issue19_complete=False,release_ready=False)
    dest=ROOT/r.EVIDENCE/os.environ['GITHUB_RUN_ID'];dest.mkdir(parents=True)
    r.write(dest/'recovery.json',receipt);r.write(r.PROOF/'recovery.json',receipt)
    for name in ('recovery-unit.stdout.txt','recovery-unit.stderr.txt'):
        (dest/name).write_bytes((r.PROOF/name).read_bytes())
    v['recovery']=dict(path=(dest/'recovery.json').relative_to(ROOT).as_posix(),binding=p.identity((dest/'recovery.json').read_bytes()),
                       proof=PROOF,screens=SCREENS,source_head=head,run_id=receipt['run_id'],original_run_id=RUN,
                       raw_verification_binding=receipt['original_verification'],commit_was_skipped=True)
    r.write(ROOT/r.CP,v);r.publish(v)
    with (ROOT/r.GUIDE).open('a') as f:
        f.write('\n## 45分中断からの原本復元\n\n原本run36138860612はcancelled、原本verificationのstatusはRUNNINGのまま保存。record/guard/artifact uploadは成功、pushはskipped。独立復元runでZIP全体digest・完全集合・source/compiled/protected binding・5caseの保存rawを照合し、元verificationを改作せず別checkpointへ投影した。欠けたfinallyのproof/screenshot indexは復元値と明示する。元run末尾のseed mtime等の一括検査完了は主張しない。未保存の進行中caseの不存在も主張しない。\n\n5件はいずれも原本50cycle、実歩数13055。正常孵化・form/初期技/PP保持・通常Save・fresh Continueを機械的に確認。10画面はフィールド復帰を目視し、個体のform/技UIの視覚受入とは区別した。保存成功5件と旧32unitは再実行していない。\n\n'+NEXT+'\n')
    state=r.load(ROOT/s.m.STATE)
    state['learnset_research_hatch']['recovery']=v['recovery']
    state['bp']['next_step']=NEXT
    state['next_action'].update(id='RESEARCH_HATCH_REMAINING_TEN',goal_ja=NEXT,read_paths=[r.GUIDE,r.CP,SELF,v['recovery']['path']])
    for path in CODE|{r.CP,r.GUIDE}:state['source_bindings'][path]=p.identity((ROOT/path).read_bytes())
    publish_resume(state)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    note=f'\n## {now}\n- Timestamp: {now}\n- Task: {r.TASK}\n- Version: interrupted-proof-recovery-v1\n- Status: STOPPED（5/15保存成功を復元、残10）\n- Summary: 元runのcancelled/RUNNING/push skippedを改称せず5ケースの原本を復元。旧32unit/host1/native5は元runの件数であり復元runの実行件数ではない。\n- Files changed: 復元driver・純proof helper・新unit・復元Actions、5件原本文書、checkpoint/guide、固定引継ぎMD/JSON、両ログ。\n- Verify: 復元runは新unit{int(count[1])}、raw純検証5、画像10のhash/目視限定。新native/旧unit/host/ARM/ROM変更0。resume check/task graph/最終index限定guardをcommit前実行。\n- Commit: 同branch非force push。source={head}。成果SHAはrecovery artifactのreflected-head.txt。\n- Network: 固定GitHub原本のみ。原本ZIP/save/ROMは非追跡。merge/release/active baseline切替なし。\n'
    for path in ('design/run_log.md','design/version_log.md'):
        with (ROOT/path).open('a') as f:f.write(note)
    print('RECOVERED: saved native PASS 5/15; old32/native/compile reruns=0')


def owned():
    import pr16_research_hatch as r
    return r.owned()|{f.relative_to(ROOT).as_posix() for f in (ROOT/r.EVIDENCE/str(RUN)).rglob('*') if f.is_file()}


def guard():
    import pr16_learnset_runtime_record as g
    import subprocess
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned();g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    actions=dict(execute=execute,guard=guard,paths=lambda:print('\n'.join(sorted(owned()))))
    p.need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|guard|paths');actions[sys.argv[1]]()
