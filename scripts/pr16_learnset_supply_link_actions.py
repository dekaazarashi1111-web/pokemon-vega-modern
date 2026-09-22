"""供給リンク原本だけのActions受入。failure専用upload以外のskipは拒否。"""
from __future__ import annotations
RUN = 35732715452
HEAD = 'abc3218f56f4bab6e97991cbfe8923b422d90f21'
PATH = '.github/workflows/pr16-learnset-supply-link-followup.yml'
JOB = 'supply-link-followup'
STEPS = ((1, 'Set up job'), (2, 'Run actions/checkout@v4'), (3, 'Run actions/setup-python@v5'),
         (4, '新供給module用ARM toolchain'), (5, '初回14試験を再利用し新ARMのmemsetだけを追加'),
         (6, 'Run actions/upload-artifact@v4'), (7, 'Run actions/upload-artifact@v4'),
         (8, 'Run actions/upload-artifact@v4'), (15, 'Post Run actions/setup-python@v5'),
         (16, 'Post Run actions/checkout@v4'), (17, 'Complete job'))


def validate_run(run, jobs):
    def need(ok, why):
        if not ok:
            raise ValueError(why)
    need(run['id'] == RUN and run['head_sha'] == HEAD and run['path'] == PATH
         and run['head_branch'] == 'codex/modernization-followup-20260908' and run['event'] == 'push'
         and run['status'] == 'completed' and run['conclusion'] == 'success', '固定run不一致')
    need(jobs['total_count'] == len(jobs['jobs']) == 1, 'job集合不一致')
    job = jobs['jobs'][0]
    need(job['id'] == 106762063715 and job['name'] == JOB and job['head_sha'] == HEAD
         and job['run_id'] == RUN and job['status'] == 'completed' and job['conclusion'] == 'success', '固定job不一致')
    need([(s['number'], s['name']) for s in job['steps']] == list(STEPS), 'step集合不一致')
    for step in job['steps']:
        want = 'skipped' if step['number'] == 8 else 'success'
        need(step['status'] == 'completed' and step['conclusion'] == want, 'step結果不一致: ' + str(step['number']))
    return {**{k: run[k] for k in ('id', 'head_sha', 'path', 'status', 'conclusion')},
            'jobs': [{**{k: job[k] for k in ('id', 'name', 'status', 'conclusion')},
                      'steps': [{k: s[k] for k in ('number', 'name', 'status', 'conclusion')} for s in job['steps']]}],
            'allowed_skip': {'number': 8, 'reason': 'failure-only artifact; success/data uploads6/7 required'}}


def completed_run(run_id, head, path, jobname):
    if (run_id, head, path, jobname) != (RUN, HEAD, PATH, JOB):
        raise ValueError('他runへのskip規約流用禁止')
    from pr16_wiki_reconcile import fetch
    return validate_run(fetch('actions/runs/' + str(RUN)), fetch('actions/runs/' + str(RUN) + '/jobs?per_page=100'))
