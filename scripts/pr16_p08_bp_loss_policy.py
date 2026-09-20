#!/usr/bin/env python3
"""旧操作で1勝した原本を保持し、第1turn後の技入力だけを変更する。"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_p08_bp_representative as m
import pr16_p08_checkpoint as c
from pr16_p08_ring_recovery import need,identity,stable,strict,archive_members
TASK='USER-20260920-P08-BPLOSS'
SELF='scripts/pr16_p08_bp_loss_policy.py'
HEADER='tools/mgba_pr16_p08_bp_loss_policy.h'
TEST='tests/test_pr16_p08_bp_loss_policy.py'
WORKFLOW='.github/workflows/pr16-p08-bp-loss.yml'
FILES=(SELF,HEADER,TEST,WORKFLOW)
BASE='26c07e15a0971af29b5b56cd8381913a89a4e333'
REPORT='content/modernization/pr16_p08_bp_loss_policy.json'
OLD_REPORT=m.REPORT
OUT=m.OUT
RUN=35510798943
JOB=106078248000
HEAD='99d93a2f4c33fb265aee5b0dc4c1ecdb697cfea1'
ARTIFACT=10605450710
ARCHIVE=dict(size=152741,sha256='da5739167b051c11dcb466e2e25e971a95f5964bb354b5e70c297b4097b6ea79')
MARKER=b'P08_BP_INPUT_CHANGE '
ADAPT=m.adapt_controller
VALIDATE=m.validate


def rank(power,split):
    need(type(power) is int and 0<=power<=255 and type(split) is int and 0<=split<=2,'move ABI')
    return 0 if split==2 else 1+power


def policy_proof(previous,current):
    before,found,tail=current.partition(MARKER)
    need(found and previous.startswith(before) and MARKER not in previous,'input changed before declared boundary')
    marker=strict(tail.splitlines()[0])
    need(set(marker)=={'frame','old_slot','new_slot'} and all(type(v) is int for v in marker.values()),'input schema')
    need(marker['frame']==3917 and marker['old_slot']==0 and 0<marker['new_slot']<4,'first changed input boundary')
    count=0
    for line in current.splitlines():
        if not line.startswith(b'P08_BP_POLICY '):continue
        matches=re.findall(rb'([a-z0-9]+)=(\d+)',line)
        fields={k.decode():int(v) for k,v in matches}
        keys={'frame','chosen'}|{p+str(i) for p in ('move','pp','power','split') for i in range(4)}
        need(len(matches)==len(fields) and set(fields)==keys and fields['frame']>=3917,'policy fields')
        eligible=[i for i in range(4) if fields['move'+str(i)] and fields['pp'+str(i)]]
        need(eligible,'no eligible moves')
        best=min(eligible,key=lambda i:rank(fields['power'+str(i)],fields['split'+str(i)]))
        need(best==fields['chosen'],'ordinary key policy differs');count+=1
    need(count>0,'policy trace missing')
    return dict(exact_byte_prefix=identity(before),first_changed_input=marker,ordinary_move_decisions=count,
                accepted_standalone_replays=0,accepted_wins_reexecuted=0,
                original_trial_wins=1,original_trial_accepted=False)


def adapt(raw,header):
    text=ADAPT(raw,header).decode()
    text=m.replace_once(text,'static void br_move(struct mCore *c,struct BPReturn *w) {',
        (ROOT/HEADER).read_text()+'\nstatic void br_move(struct mCore *c,struct BPReturn *w) {')
    old='''    for(unsigned i=0;i<4U;++i){
        unsigned m=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*i);
        unsigned p=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+i);
        if(m && p){slot=i;move=m;pp=p;break;}
    }'''
    new='''    slot=p08_loss_slot(c);
    move=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*slot);
    pp=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+slot);'''
    return m.replace_once(text,old,new).encode()


def validate(raw,stderr,proc):
    row=VALIDATE(raw,stderr,proc)
    value=policy_proof((OUT/'previous.stderr').read_bytes(),stderr)
    (OUT/'policy-proof.json').write_bytes(stable(value))
    return row


def configure():
    m.REPORT=REPORT;m.FILES=(*FILES,*m.FILES);m.TASK=TASK
    m.adapt_controller=adapt;m.validate=validate


def prepare():
    b=c.b;b.OUT=OUT;head=b.scope();b.resume.validate(ROOT);OUT.mkdir(parents=True,exist_ok=True)
    need(not (ROOT/REPORT).exists(),'already attempted: read current result')
    need(set(b.command('git','diff','--name-only',BASE,head).splitlines())==set(FILES),'source scope')
    run=b.api('actions/runs/'+str(RUN));job=b.api('actions/jobs/'+str(JOB));art=b.api('actions/artifacts/'+str(ARTIFACT))
    need(run['head_sha']==HEAD and run['status']=='completed' and run['conclusion']=='failure','old run')
    need(job['run_id']==RUN and job['status']=='completed' and job['conclusion']=='failure','old job')
    need(not art['expired'] and art['workflow_run']['id']==RUN and art['digest']=='sha256:'+ARCHIVE['sha256'],'old artifact')
    raw=subprocess.check_output(['gh','api','repos/'+b.REPO+'/actions/artifacts/'+str(ARTIFACT)+'/zip'],cwd=ROOT)
    members=archive_members(raw,ARCHIVE);old=strict(members['native-result.json'])
    need(old['candidate']==m.TARGET and old['new_emulator_processes']==1 and not old['native_verified']
         and old['failures']==[dict(type='ValueError',message='native process not successful')],'old failure boundary')
    prev=members['execution/'+m.CASE+'.stderr']
    need(prev.endswith(b'P03 archive: P08 requires native loss representative\n')
         and b'outcome=1' in prev and members['execution/'+m.CASE+'.stdout']==b'','not the unexpected-win boundary')
    (OUT/'previous.stderr').write_bytes(prev)
    for path,expected in {**old['source_bindings'],**old['protected_originals']}.items():
        need(identity((ROOT/path).read_bytes())==expected,'old/protected source drift: '+path)
    original=m.originals(b)
    _,err,proc=b.capture([sys.executable,'-m','unittest','discover','-s','tests','-p',Path(TEST).name,'-v'],'policy-tests')
    need(b.exited(proc)==0 and b'\nOK\n' in err,'policy contract failure')
    value=copy.deepcopy(old)
    for key in ('process','generated','transitive_compiled_sources','loss_entry'):value.pop(key,None)
    value.update(task=TASK,source_head=head,workflow_source_head=os.environ['GITHUB_SHA'],original=original,
        previous_trial=dict(run_id=RUN,job_id=JOB,head_sha=HEAD,artifact_id=ARTIFACT,archive=ARCHIVE,
            conclusion='failure',classification='UNEXPECTED_NATIVE_WIN_NOT_LOSS_ACCEPTANCE',new_processes=1,
            observed_fresh_cores=1,accepted=False,report=OLD_REPORT),
        source_bindings={p:identity((ROOT/p).read_bytes()) for p in m.FILES},
        new_emulator_processes=0,host_compiles=0,fresh_cores=0,failures=[],screens={})
    value['protected_originals'][OLD_REPORT]=identity((ROOT/OLD_REPORT).read_bytes())
    (OUT/'native-result.json').write_bytes(stable(value))
    m.checkpoint(value,'START')


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');configure()
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='native':m.native()
    elif sys.argv[1]=='finish':m.checkpoint(strict((OUT/'native-result.json').read_bytes()),'FINISH')
    elif sys.argv[1]=='pack':c.pack(OUT,m.FILES)
    elif sys.argv[1]=='result':sys.exit(0 if strict((OUT/'native-result.json').read_bytes())['native_verified'] else 1)
    else:raise ValueError('unknown command')
