#!/usr/bin/env python3
"""0processの修正3ファイルだけを旧commitと照合し、固定引継ぎhashを更新する。"""
from pathlib import Path
import json
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_win_return_trace as task
SELF='scripts/pr16_circus_trace_bindings.py'
WORKFLOW='.github/workflows/pr16-circus-trace-bindings.yml'
TEST='tests/test_pr16_circus_trace_bindings.py'
OLD_HEAD='b5e22ea1a7fddc30a2c705e2fafffeb3648fd8c9'
PATHS=(task.SELF,task.HEADER,task.TEST)


def refresh(state,old,current):
    import copy
    need=task.need;need(set(old)==set(current)==set(PATHS),'binding repair scope differs')
    value=copy.deepcopy(state)
    for name in PATHS:
        need(value['source_bindings'][name]==task.identity(old[name]),'old accepted source binding differs: '+name)
        need(task.identity(current[name])!=task.identity(old[name]),'binding repair no change: '+name)
        value['source_bindings'][name]=task.identity(current[name])
    return value


def configure():
    task.FILES=tuple(dict.fromkeys((*task.FILES,task.SELF,SELF,WORKFLOW,TEST)))
    # SELFは診断モジュールの再importにも使う。pipelineは元の診断入口で実行できる。
    # ラッパーのpathへ置換するとhost testが別モジュールを読みnative前に失敗する。
    task.WORKFLOW=WORKFLOW


def prepare():
    import pr16_resume as resume
    r=task.configure().rec;r.scope()
    old={p:subprocess.check_output(['git','show',OLD_HEAD+':'+p],cwd=ROOT) for p in PATHS}
    current={p:(ROOT/p).read_bytes() for p in PATHS}
    state=resume.load(ROOT,resume.STATE)
    value=refresh(state,old,current)
    failed=r.api('actions/runs/35431388329');jobs=r.api('actions/runs/35431388329/jobs')['jobs']
    task.need(failed['status']=='completed' and failed['conclusion']=='failure' and failed['head_sha']=='7fbe8149bac5c3442314d51694d33a335bfcdeb4'
        and len(jobs)==1 and jobs[0]['id']==105866524966 and jobs[0]['steps'][2]['conclusion']=='failure'
        and jobs[0]['steps'][3]['conclusion']=='skipped','binding failure source differs')
    host_failed=r.api('actions/runs/35431539401');host_jobs=r.api('actions/runs/35431539401/jobs')['jobs']
    task.need(host_failed['status']=='completed' and host_failed['conclusion']=='failure'
        and host_failed['head_sha']=='ab95c9f172ad0e453c591f94c54efd54bc88f115'
        and len(host_jobs)==1 and host_jobs[0]['id']==105866926442
        and host_jobs[0]['steps'][2]['conclusion']=='failure' and host_jobs[0]['steps'][3]['conclusion']=='skipped',
        'configured host test failure source differs')
    value['circus_trace_binding_repair']=dict(old_head=OLD_HEAD,changed_paths=list(PATHS),
        before={p:task.identity(old[p]) for p in PATHS},after={p:task.identity(current[p]) for p in PATHS},
        failed_run=35431388329,failed_job=105866524966,original_conclusion='failure',native_processes=0,
        configured_host_test_failure=dict(run_id=35431539401,job_id=105866926442,native_processes=0,
            original_conclusion='failure',reason_ja='wrapperがSELFを置換し診断再import testが別moduleを参照。SELF不変とconfigure二重呼出しを回帰検査。'),
        reason_ja='macro修正3ファイルに固定resumeの旧hashが残りprepareで拒否。旧commitの3原本と完全一致を確認して対象3hashだけ更新。他のbinding/受入結果は変更しない。')
    value['do_not_repeat'].insert(0,'run35431388329は固定resumeの旧source hashでprepare停止、native0。3ファイルの旧commit照合だけで更新し、ゲームの受入を変えない。')
    value['do_not_repeat'].insert(0,'run35431539401/job105866926442はconfigure後の診断module再import testでprepare停止、native0。wrapperのSELF置換を修復して未実行readonly診断へ進む。旧failureを成功へ読み替えない。')
    r.tests([Path(TEST).name])
    (ROOT/resume.STATE).write_bytes(task.stable(value));(ROOT/resume.DOC).write_text(resume.render(value))
    resume.validate(ROOT);configure();task.prepare()


if __name__=='__main__':
    task.need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action=='prepare':prepare()
    else:
        configure()
        if action=='pipeline':task.configure().pipeline()
        elif action=='pack':task.configure();task.c.f.pack()
        elif action in {'reconstruct','native','finish'}:getattr(task,action)()
        else:raise SystemExit('unknown command')
