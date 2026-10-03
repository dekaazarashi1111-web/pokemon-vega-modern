#!/usr/bin/env python3
"""観測前fixtureの歩行だけを修復。BG/menu/Save/Continue契約は変更しない。"""
from __future__ import annotations
import datetime
import hashlib
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_collection_gift_step.py'
TEST='tests/test_pr16_collection_gift_step.py'
C='tools/mgba_pr16_collection_gifts.c'
BEFORE='80b3ace6b3e85853b3ab2f40bd39ba737d081a9f48e0552b26f4758968397662'
REPLACEMENTS=(
 ('    b_position(c,CF_GROUP,CF_NUMBER,CF_X,CF_Y+1U);\n',
  '    b_state(c,"fixture-warp");b_position(c,CF_GROUP,CF_NUMBER,CF_X,CF_Y+1U);\n'),
 ('    cf_press(c,QOL_KEY_UP,30U);b_position(c,CF_GROUP,CF_NUMBER,CF_X,CF_Y);cf_fixture_owner(c);',
  '    b_step(c,QOL_KEY_UP);b_state(c,"fixture-approach");b_position(c,CF_GROUP,CF_NUMBER,CF_X,CF_Y);cf_fixture_owner(c);'))

def need(ok,text):
    if not ok:raise ValueError(text)

def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def normalized_controller(raw):
    """既受入host検査の対象は不変。置換はguardより前だけ、元C完全hashまで照合。"""
    text=raw.decode();before,after=text.split('cf_t.boundary=b_frames;',1)
    for old,new in REPLACEMENTS:
        need(before.count(new)==1 and new not in after and old not in before,'fixture一意/guard前')
        before=before.replace(new,old)
    original=(before+'cf_t.boundary=b_frames;'+after).encode()
    need(identity(original)['sha256']==BEFORE,'fixture以外のC変更禁止')
    return original


def prepare():
    from pr16_learnset_compact_record import publish_resume
    from pr16_collection_gift_native import load_runtime
    import pr16_learnset_runtime_record as g
    from pr16_learnset_wiki_actions import current
    current();scope,c=load_runtime();head=os.environ['GITHUB_SHA'];run=int(os.environ['GITHUB_RUN_ID'])
    old=c.load(ROOT/c.CP);need(old['run_id']==36118704240 and not old['accepted'],'未受入fixture停止点')
    stderr=(ROOT/c.EVIDENCE/'36118704240/fixed-form-1254.stderr.txt').read_bytes()
    need(stderr==b'P03 archive: breeding physical map/position differs\n','配布前位置停止の原本')
    raw=(ROOT/C).read_bytes();need(identity(raw)['sha256']==BEFORE,'固定C入力')
    text=raw.decode()
    for before,after in REPLACEMENTS:
        need(text.count(before)==1,'fixture置換一意');text=text.replace(before,after)
    (ROOT/C).write_text(text);need(normalized_controller(text.encode())==raw,'変更境界完全一致')
    result=subprocess.run([sys.executable,'-B','-m','unittest','tests.test_pr16_collection_gift_step','-v'],cwd=ROOT,capture_output=True)
    sys.stderr.buffer.write(result.stderr)
    need(result.returncode==0 and b'Ran 1 test' in result.stderr and b'\nOK\n' in result.stderr,'新fixture契約1試験')
    dest=ROOT/c.EVIDENCE/str(run);dest.mkdir(parents=True)
    proof=dict(task='USER-20260925-COLLECTION-STEP',status='PASS_PRE_BARRIER_STEP_REPAIR_NATIVE_PENDING',
      input_head=head,run_id=run,modified_source_after_input_head=True,new_unit_tests=1,old_unit_reruns=0,
      old_native_reruns=0,new_native_processes=0,host_compiles=0,arm_compiles=0,rom_changes=0,
      prior_run=36118704240,source_before=identity(raw),source_after=identity(text.encode()),
      guarded_controller_bytes_unchanged=True,old_suite_coverage_unchanged=True,issue19_complete=False,release_ready=False)
    c.write(dest/'step-repair.json',proof);(dest/'step-unit.stderr.txt').write_bytes(result.stderr)
    state=c.load(ROOT/c.m.STATE);state['learnset_collection_gift_step']=dict(path=(dest/'step-repair.json').relative_to(ROOT).as_posix(),**proof)
    goal='Collection BG検出は通過。初期fixtureの方向入力を座標変化を待つ1マス歩行へ修復。未受入17配布を次に実行。旧24/scope9/cache5と受入済みnativeは再実行しない。'
    state['bp']['current_stop']='Collection最初の配布前位置確認で停止。fixture歩行修復1試験PASS、nativeは未検証。'
    state['bp']['next_step']=goal;state['next_action']=dict(state['next_action'],id='COLLECTION_GIFTS_BG_NATIVE',goal_ja=goal)
    for p in c.CODE|{SELF,TEST}:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    note=f'\n## {now}\n- Timestamp: {now}\n- Task: USER-20260925-COLLECTION-STEP\n- Version: collection-fixture-step-v1\n- Status: DONE（観測前fixture修復限定、native未完）\n- Summary: run36118704240はBG照合/host compile通過、native1は配布前の位置確認で停止。残り16未実行、旧unit/scope再実行0。2frame方向入力を既存b_stepの座標変化待ちへ修復しwarp/接近の位置ログを追加。\n- Files changed: Cのguard前2箇所、歩行境界検査、unit継承の正規化証明、固定引継ぎMD/JSON、原本text、両ログ。\n- Verify: 新fixture1試験PASS。guard後Cはbyte不変、逆置換で前Cの完全SHA一致。配布/menu/Save/ContinueやROMを変えていない。旧24/scope9/cache5/nativeの再実行0。\n- Commit: 同branchへの非force commit/push・remote照合。成果SHAはreflected-head.txt。\n- Network: GitHub固定原本/Actions。ROM/seed非追跡。merge/release/baseline切替なし。\n'
    for p in ('design/run_log.md','design/version_log.md'):
        with (ROOT/p).open('a') as f:f.write(note)
    for command in ([sys.executable,'-B','scripts/pr16_resume.py','check'],[sys.executable,'-B','scripts/validate_task_graph.py']):
        subprocess.run(command,cwd=ROOT,check=True)
    owned={C,c.m.STATE,c.m.DOC,'design/run_log.md','design/version_log.md'}|{p.relative_to(ROOT).as_posix() for p in dest.iterdir()}
    subprocess.run(['git','add','--',*sorted(owned)],cwd=ROOT,check=True)
    g.START=head;g.CODE={C};g.OWNED=owned-{C};g.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    out=ROOT/'.local/pr16-collection-step';out.mkdir(parents=True);c.write(out/'verification.json',proof)

if __name__=='__main__':prepare()
