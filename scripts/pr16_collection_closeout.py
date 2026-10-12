#!/usr/bin/env python3
"""Collection17の原本継承と目視記録を照合し、終端だけ確定。native実行なし。"""
from __future__ import annotations
import datetime
import io
import os
from pathlib import Path
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_collection_closeout.py'
REVIEW='content/modernization/pr16_collection_visual_review_20260925.json'


def execute():
    import pr16_collection_gift_observation as o
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_wiki_actions import current
    from pr16_learnset_compact_record import publish_resume
    n,scope,c=o.install();c.CODE|={SELF,REVIEW};head=current()
    v=c.load(ROOT/c.CP);review=c.load(ROOT/REVIEW)
    o.need(v['run_id']==review['run_id'] and v['source_head']==review['source_head'] and len(v['accepted'])==17 and not v['failures'],'17実測と目視のsource対応')
    previous=c.load(ROOT/c.EVIDENCE/'36119380600/verification.json')
    origins={name:row for name,row in v['accepted'].items() if row['run_id']==36119380600}
    o.need(set(origins)=={'fixed-form-1254','fixed-form-1390','research-egg-1201'},'継承3件集合')
    for name in ('fixed-form-1254','fixed-form-1390'):
        o.need(origins[name]==previous['accepted'][name],'既受入caseの原本不変 '+name)
    original_revalidation=c.load(ROOT/c.EVIDENCE/'36120941191/revalidated-1201.json')
    o.need(origins['research-egg-1201']==original_revalidation,'1201の再検証原本不変')
    for name,row in v['accepted'].items():
        o.need(row['run_id'] in (36119380600,v['run_id']),'未把握のnative origin')
        o.need(row['result']['status']=='PASS' and not row['result']['egg_hatch_verified'] and not row['result']['story_acquisition_verified'],'限定受入の境界')
    artifacts=fetch('actions/runs/'+str(v['run_id'])+'/artifacts?per_page=100')
    o.need(artifacts['total_count']==len(artifacts['artifacts']),'artifactページ完全性')
    matches=[a for a in artifacts['artifacts'] if a['name']=='pr16-collection-gifts-screens']
    o.need(len(matches)==1,'画面artifact一意');a=matches[0]
    o.need(not a['expired'] and a['workflow_run']['head_sha']==v['source_head'],'画面原本のsource')
    o.need({k:a[k] for k in ('id','digest','size_in_bytes')}==review['artifact'],'目視済みZIP identity')
    raw=fetch('actions/artifacts/'+str(a['id'])+'/zip',binary=True)
    o.need(o.identity(raw)==dict(sha256=a['digest'][7:],size=a['size_in_bytes']),'画面ZIP完全SHA')
    expected={name+'-'+stage+'.ppm' for name in v['accepted'] if name not in origins for stage in ('selected','received','continued')}
    reviewed={name+'-'+stage+'.ppm' for name in review['case_labels'] for stage in review['stages']}
    o.need(len(expected)==42 and reviewed==expected and set(v['screenshots'])==expected,'42枚の対象集合')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        o.need(len(z.namelist())==len(expected) and set(z.namelist())==expected,'画面ZIP重複/余剰なし')
        for name in sorted(expected):
            raw=z.read(name);integrity=o.image_integrity(raw)
            o.need(o.identity(raw)==v['screenshots'][name],'目視フレーム原本hash '+name)
    o.need(review['mechanical_cases']==17 and review['rendered_cases']==14 and review['excluded_blank_frames']==9 and not review['all_routes_visual_acceptance'],'目視の限定範囲')
    # original rawのaccepted集合を変えず、独立した目視原本への参照だけ追加する。
    v['visual_review']=dict(path=REVIEW,binding=o.identity((ROOT/REVIEW).read_bytes()),
                           rendered_cases=14,reviewed_frames=42,excluded_blank_frames=9,all_routes_visual_acceptance=False)
    c.write(ROOT/c.CP,v)
    n.complete()
    v=c.load(ROOT/c.CP)
    note='\n## 終端確定と再開境界\n\n学習owner17/17の配布・初期4技/PP・通常Save・fresh-core Continue・再訪取消を限定受入。うち14件の42画像は保存ZIPと全フレームhashを照合して目視記録へ結合。先行3件の黒画像9枚は除外したまま。原本1281、ストーリー獲得、研究タマゴ孵化、特殊野生、Issue19全体、releaseはこの受入に含めない。\n\nこの17件や旧受入を理由なく再実行しない。状態JSONの次作業は特殊野生と研究タマゴ孵化の未受入経路。今回の機械実測入口は `scripts/pr16_collection_gift_observation.py`、終端確定は `scripts/pr16_collection_closeout.py`。直接旧18件driverを再実行しない。\n'
    with (ROOT/c.GUIDE).open('a') as f:f.write(note)
    state=c.load(ROOT/c.m.STATE)
    state['learnset_collection_visual_review']=v['visual_review']
    state['source_bindings'][c.GUIDE]=o.identity((ROOT/c.GUIDE).read_bytes())
    for path in (SELF,REVIEW):state['source_bindings'][path]=o.identity((ROOT/path).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {now}\n- Timestamp: {now}\n- Task: USER-20260925-COLLECTION-GIFTS\n- Version: collection-learning-scope-terminal-v1\n- Status: DONE（学習owner17/17限定、Issue19/release未完）\n- Summary: 先行3件の機械的受入原本不変、未受入14件のみ追加実測。14件42画像を原本SHAで目視記録に結合し、先行黒画像9枚は視覚受入から除外。全Actions終端/最新proof ZIP/反映commit親/各raw証拠/source不変を照合。\n- Files changed: 終端照合器、目視JSON、Collection checkpoint/guide/text受領証、固定引継ぎMD/JSON、両ログ。\n- Verify: この終端runのnative/旧unit/host/ARM/ROM変更0。受入済み再実行0。resume check/task graph/final-index scoped private guardをcommit前実行。\n- Commit: 同branchへ非force commit/push・remote照合。成果SHAはterminal artifactのreflected-head.txt。\n- Network: GitHubの保存Actions/artifact原本照合のみ。ROM/save非追跡。merge/release/active baseline切替なし。1281 identity-only/自動fallback禁止を維持。\n'
    for path in ('design/run_log.md','design/version_log.md'):
        with (ROOT/path).open('a') as f:f.write(log)
    dest=ROOT/c.EVIDENCE/os.environ['GITHUB_RUN_ID']
    receipt=dict(task=c.TASK,status='PASS_COLLECTION_17_TERMINAL_WITH_SCOPED_VISUAL_REVIEW',
      input_head=head,run_id=int(os.environ['GITHUB_RUN_ID']),mechanical_cases=17,
      original_native_runs=sorted({r['run_id'] for r in v['accepted'].values()}),
      rendered_cases=14,reviewed_frames=42,excluded_blank_frames=9,visual_review=v['visual_review'],
      reviewed_frame_bindings=v['screenshots'],
      new_native_processes=0,new_unit_tests=0,host_compiles=0,arm_compiles=0,rom_changes=0,
      terminal_actions=v['terminal_actions'],proof_artifact=v['proof_artifact'],
      issue19_complete=False,release_ready=False,active_baseline_changed=False)
    c.write(dest/'visual-terminal.json',receipt);c.write(c.PROOF/'visual-terminal.json',receipt)

if __name__=='__main__':execute()
