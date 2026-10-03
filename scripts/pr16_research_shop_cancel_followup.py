#!/usr/bin/env python3
"""入力seamのみの再試験。成功済み20oracleと失敗native原本を保存して再利用。"""
from __future__ import annotations
import io
import os
from pathlib import Path
import sys
import zipfile
import pr16_research_shop_cancel_actions as a
SELF='scripts/pr16_research_shop_cancel_followup.py'
FAILED_RUN=36246971189
FAILED_HEAD='3cb13d02f548be5d4770bd3807d3bc74c98b39f7'
ARTIFACT_ID=10908270748
ARCHIVE={'size':15389,'sha256':'2385dc761e60075986f638979967702f06da8b3b98c6f3eddc619c3782a94db8'}
original_unit=a.unit
original_publish=a.publish
a.OWN_SOURCE.add(SELF)
# 共通記録器が列挙する正本Cのpath。検証対象コードの変更ではない。
a.m.prior.SOURCE='overlays/research_economy_v1/research_economy_v1.c'

def unit(sources):
    a.need(os.environ.get('REUSE_UNIT_RUN')==str(FAILED_RUN),'reuse exact successful20; no rerun')
    # このwrapperとC入力pulseはfixture/validator20の依存ではない。
    original_unit({p:b for p,b in sources.items() if p!=SELF})
    run=a.d.inputs.api('actions/runs/'+str(FAILED_RUN))
    a.need(run['head_sha']==FAILED_HEAD and run['conclusion']=='failure','keep failed run conclusion')
    raw=a.d.inputs.api('actions/artifacts/'+str(ARTIFACT_ID)+'/zip',True)
    a.need(a.identity(raw)==ARCHIVE,'immutable original failed archive')
    required=('native.stdout.txt','native.stderr.txt','native-process.json','compile.json','guards.json','inputs.json','invocation.json')
    copied={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for name in required:
            b=z.read(name);a.need(len(b)<=500000 and b'\0' not in b,'bounded previous text');b.decode('utf-8')
            target='prior-'+str(FAILED_RUN)+'-'+name;(a.d.PUBLIC/target).write_bytes(b);copied[target]=a.identity(b)
    a.d.put('previous-failed-run.json',{'run':a.d.run_summary(run),'archive':ARCHIVE,'artifact_id':ARTIFACT_ID,'copies':copied,'old_native_accepted':False,'failure':'normal next page action','old_unit_tests':20,'new_unit_tests':0,'changed_scope':'two-frame input pulse and menu settling only; real cancel trace affected'})

def publish(cp,evidence):
    cp['new_unit_tests']=0;cp['reused_unit_tests']=20;cp['unit_reuse_run_id']=FAILED_RUN
    cp['previous_failed_runs']=[{'run_id':FAILED_RUN,'head_sha':FAILED_HEAD,'conclusion':'failure','native_accepted':False,'artifact':ARCHIVE}]
    cp['entrypoint']=SELF
    original_publish(cp,evidence)
    guide=a.ROOT/a.GUIDE
    with guide.open('a') as f:
        f.write('\n## 入力seam修正と原本の分離\n\n初回run `36246971189` は20oracleとcompile/guard、実背景→B取消まで通過したが次ページ確認で失敗。1frame押下から既存qol_press相当の2frame押下/受付settleへ変更した新driverだけを再実行し、元runを成功に改変しない。成功済み20件は依存hash照合で再利用し、再実行0。旧native stdout/stderr/process/compile/guard/inputs/invocationはprefix付き原本として新manifestに保存。今回のnative1/host compile1は受入run単体の値で、初回失敗分を消した総数ではない。エントリは `'+SELF+'`。\n')
    state=a.d.read(a.ROOT/a.d.STATE);state['source_bindings'][a.GUIDE]=a.identity(guide.read_bytes())
    state['next_action']['read_paths'].append(SELF)
    from pr16_learnset_compact_record import publish_resume
    publish_resume(state)
    for path in a.d.LOGS:
        with (a.ROOT/path).open('a') as f:f.write('- Input followup: 初回36246971189はfailure保持。新driver入力seam変更のみ。20oracleは原本再利用/再実行0、旧native原本はimmutable prefix付き証拠。\n')

a.unit=unit;a.publish=publish
if __name__=='__main__':
    if sys.argv[1:]==['measure']:a.measure()
    elif sys.argv[1:]==['finalize']:a.finalize()
    elif sys.argv[1:]==['guard']:a.guard()
    else:raise SystemExit('measure | finalize | guard')
