#!/usr/bin/env python3
"""Collection観測: 先頭cursor同時刻の限定許容、描画初期化、原本再検証。"""
from __future__ import annotations
from copy import deepcopy
import datetime
import hashlib
import importlib
import io
import zipfile
import json
import os
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_collection_gift_observation.py'
TEST='tests/test_pr16_collection_gift_observation.py'
DRIVER='scripts/pr16_collection_gifts.py'
C='tools/mgba_pr16_collection_gifts.c'
OLD_DRIVER='f36ede0b0046eaf86b9f8c685fad22ca20cbbac3180d7931b9a5231957dc6fcf'
OLD_C='50836c4a0a32d67182b1ca04f47c6c40ec4c6aaa799b6e0b7ac76af7b507d59d'
OLD_CHECK="""    need(all(type(t[k]) is int for k in keys) and 0 < t[keys[0]] and
         all(t[a] < t[b] for a,b in zip(keys, keys[1:])) and t['cancelled'] < 150000, 'strict physical chronology')"""
NEW_CHECK="""    from pr16_collection_gift_observation import chronology
    chronology(t, case, geo, err)"""
RENDER=(
 ('c->setVideoBuffer(c,b_video,240U);\n    a_require(a_continue(c)',
  'c->setVideoBuffer(c,b_video,240U);c->reset(c);\n    a_require(a_continue(c)'),
 ('c=b_restart(c,argv[1],argv[2]);saved=*c;a_guard(c);',
  'c=b_restart(c,argv[1],argv[2]);c->reset(c);saved=*c;a_guard(c);'))
KEYS=('boundary','root','list','selected','claimed','returned','saved','continued','revisited','cancelled')
TASK='USER-20260925-COLLECTION-OBSERVATION'


def need(ok,message):
    if not ok:raise ValueError(message)


def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def chronology(t,case,geo,err):
    need(type(t) is dict and set(t)==set(KEYS) and all(type(t[k]) is int for k in KEYS), '観測時刻の厳密型')
    need(0<t['boundary'] and t['cancelled']<150000,'観測時刻の境界')
    for a,b in zip(KEYS,KEYS[1:]):
        if (a,b)==('list','selected') and t[a]==t[b]:
            # selectedはAを押す前のcursor確認。最初の行では移動0frame。
            need(type(case['gift_index']) is int and case['gift_index']==0,'同時刻は最初のgiftのみ')
            pattern=(rb'^BREED menu map=(\d+)/(\d+) xy=(\d+),(\d+) [^\n]* frame=(\d+) [^\n]*\n'
                     rb'CF_UI stage=menu mode=3 page=0 window=\d+ cursor=0 result=9 pending=65535 host=(\d+) service=5 test=0 lock=1$')
            rows=[tuple(map(int,row)) for row in re.findall(pattern,err,re.M)]
            wanted=(geo['group'],geo['number'],geo['x'],geo['y'],t['list'],geo['host_index'])
            need(rows.count(wanted)==1,'原本menuの初期cursor/host/座標/frameが必要')
        else:need(t[a]<t[b], 'strict physical chronology '+a+'/'+b)


def reverse(raw,replacements,sha):
    text=raw.decode()
    for old,new in replacements:
        need(text.count(new)==1 and old not in text,'一意の観測修復差分')
        text=text.replace(new,old)
    restored=text.encode();need(identity(restored)['sha256']==sha,'観測修復以外の変更を拒否')
    return restored


def normalized_driver(raw):return reverse(raw,((OLD_CHECK,NEW_CHECK),),OLD_DRIVER)
def normalized_render(raw):return reverse(raw,RENDER,OLD_C)


def image_integrity(raw):
    header=b'P6\n240 160\n255\n'
    need(raw.startswith(header) and len(raw)==len(header)+240*160*3,'PPM形状')
    pixels=raw[len(header):];colors=len({pixels[i:i+3] for i in range(0,len(pixels),3)})
    need(colors>1,'単色画像は画面証拠ではない')
    return dict(identity(raw),distinct_colors=colors,visual_semantics_accepted=False)


def runtime():
    import pr16_collection_gift_native as n
    scope,c=n.load_runtime();c.CODE|={SELF,TEST}
    return n,scope,c


def publish(scope,c,v,completion=False):
    original=scope._observation_original_publish
    original(v,completion)
    from pr16_learnset_compact_record import publish_resume
    note='\n## 観測原本の適用範囲\n\nrun36119380600の固定2件と研究1201はheadless実測の機械的受入。保存画像9枚は単色のため画面受入に使わない。1201は先頭cursorと一覧表示が同frameになる誤拒否を、raw menu/frameを追加照合して原本再検証した。失敗run/原本は成功へ書き換えていない。この3件を再実行せず、残りだけ描画初期化後の別controller identityで実行する。画像の非単色検査と意味内容の目視確認を区別する。\n'
    with (ROOT/c.GUIDE).open('a') as f:f.write(note)
    state=c.load(ROOT/c.m.STATE)
    if 'observation_repair' in v:state['learnset_collection_observation']=v['observation_repair']
    state['source_bindings'][c.GUIDE]=identity((ROOT/c.GUIDE).read_bytes())
    for p in c.CODE:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    publish_resume(state)


def install():
    n,scope,c=runtime()
    if not hasattr(scope,'_observation_original_publish'):
        scope._observation_original_publish=scope.publish
        scope.publish=lambda v,completion=False:publish(scope,c,v,completion)
    return n,scope,c


def prepare():
    from pr16_learnset_wiki_actions import current
    from pr16_wiki_reconcile import fetch
    import pr16_learnset_runtime_record as guard
    n,scope,c=runtime();head=current();run=int(os.environ['GITHUB_RUN_ID'])
    old=c.load(ROOT/c.CP)
    need(old['run_id']==36119380600 and set(old['accepted'])=={'fixed-form-1254','fixed-form-1390'},'固定した停止点')
    need(old['failures']=={'research-egg-1201':dict(error='strict physical chronology',type='ValueError')},'時刻検証だけの失敗原本')
    before={p:(ROOT/p).read_bytes() for p in (DRIVER,C)}
    need(identity(before[DRIVER])['sha256']==OLD_DRIVER and identity(before[C])['sha256']==OLD_C,'固定source')
    text=before[DRIVER].decode();need(text.count(OLD_CHECK)==1,'時刻検査一意')
    (ROOT/DRIVER).write_text(text.replace(OLD_CHECK,NEW_CHECK))
    text=before[C].decode()
    for a,b in RENDER:
        need(text.count(a)==1,'描画初期化一意');text=text.replace(a,b)
    (ROOT/C).write_text(text)
    normalized_driver((ROOT/DRIVER).read_bytes());normalized_render((ROOT/C).read_bytes())
    result=subprocess.run([sys.executable,'-B','-m','unittest','tests.test_pr16_collection_gift_observation','-v'],cwd=ROOT,capture_output=True)
    sys.stderr.buffer.write(result.stderr)
    need(result.returncode==0 and b'Ran 6 tests' in result.stderr and b'\nOK\n' in result.stderr,'新観測6unit')
    c=importlib.reload(c);n,scope,c=install()
    name='research-egg-1201';contract=old['contracts'][name]
    raw={}
    for suffix in ('stdout.txt','stderr.txt','process.json'):
        filename=name+'.'+suffix;raw[suffix]=(ROOT/old['evidence_path']/filename).read_bytes()
        need(identity(raw[suffix])==old['public_evidence_bindings'][filename],'保存rawのhash '+suffix)
    need(json.loads(raw['process.json'])==dict(returncode=0,timed_out=False),'native実行自体の成功')
    accepted=c.validate(raw['stdout.txt'],raw['stderr.txt'],contract['case'],contract['geometry'])
    native_run=fetch('actions/runs/36119380600')
    need(native_run['status']=='completed' and native_run['conclusion']=='failure' and native_run['head_sha']==old['source_head'],'失敗runを保持')
    screen_zip=fetch('actions/artifacts/10856621674/zip',binary=True)
    need(identity(screen_zip)==dict(size=2677,sha256='a048d4b99a19af139ab76817254e4d6dfe6e5aa7dd25f2fe1a867eb4b23c1046'),'旧画面ZIP原本')
    with zipfile.ZipFile(io.BytesIO(screen_zip)) as z:
        need(len(z.namelist())==9,'旧画像9枚')
        for filename in z.namelist():
            b=z.read(filename);header=b'P6\n240 160\n255\n'
            need(b.startswith(header) and len(b)==len(header)+240*160*3 and not any(b[len(header):]),'旧画像は黒一色')
    v=deepcopy(old)
    v['accepted'][name]=dict(contract=contract,result=accepted,run_id=old['run_id'],source_head=old['source_head'],
       validation_source=head,validation_kind='ORIGINAL_NATIVE_RAW_REVALIDATED_NO_RERUN')
    v['failures']={};v.pop('error',None);v.pop('error_type',None)
    v['pending_cases']=[x for x in v['contracts'] if x not in v['accepted']]
    dest=ROOT/c.EVIDENCE/str(run);dest.mkdir(parents=True)
    proof=dict(schema_version=1,task=TASK,status='PASS_OBSERVATION_REPAIR_THREE_MECHANICAL_CASES',input_head=head,run_id=run,
      modified_source_after_input_head=True,new_unit_tests=6,old_unit_reruns=0,new_native_processes=0,accepted_case_reruns=0,
      host_compiles=0,arm_compiles=0,rom_changes=0,native_origin_run=36119380600,original_run_conclusion='failure',
      accepted_original_cases=list(v['accepted']),revalidated_case=name,
      raw_bindings={k:identity(b) for k,b in raw.items()},controller_before=identity(before[C]),controller_after=identity((ROOT/C).read_bytes()),
      driver_before=identity(before[DRIVER]),driver_after=identity((ROOT/DRIVER).read_bytes()),
      observation_source_bindings={p:identity((ROOT/p).read_bytes()) for p in (SELF,TEST)},
      previous_screens=dict(run_id=36119380600,artifact_id=10856621674,images=9,all_single_color=True,visual_acceptance=False),
      render_fix_scope='RESET_AFTER_VIDEO_BUFFER_BEFORE_EACH_BOOT_CONTINUE_NO_GIFT_LOGIC_CHANGE',
      primary_source='mgba-emu/mgba@0.10.2:src/gba/core.c:_GBACoreReset (blob 8bdf218b3e3b8a73d4da4c1b028ae86843f3a502)',
      issue19_complete=False,release_ready=False)
    c.write(dest/'observation-repair.json',proof);c.write(dest/'revalidated-1201.json',v['accepted'][name])
    (dest/'observation-unit.stderr.txt').write_bytes(result.stderr)
    v['observation_repair']=dict(path=(dest/'observation-repair.json').relative_to(ROOT).as_posix(),**proof)
    c.write(ROOT/c.CP,v);scope.publish(v)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    note=f'\n## {now}\n- Timestamp: {now}\n- Task: {TASK}\n- Version: collection-observation-v1\n- Status: DONE（時刻検査・描画初期化修復と3件の機械的受入、残り14native未完）\n- Summary: 先頭giftのみlist==selectedをraw cursor/host/座標/frameで厳密照合。他時刻はstrictのまま。研究1201の保存stdout/stderr/processを再検証し3/17へ。元run36119380600のfailure・旧raw・固定2受入は不変。9単色PPMは視覚証拠から除外。\n- Files changed: driver時刻検査、Cの2boot描画reset、新観測module/unit、checkpoint/guide、固定MD/JSON、text証拠、両ログ。\n- Verify: 新6unit PASS、1201原本再検証1、native/host/ARM/ROM変更0、旧受入再実行0。両sourceを逆置換し修復前完全SHAを照合。画像resetは残り未受入ケースで実測する。\n- Commit: 同branchへ非force commit/push・remote照合。\n- Network: read-only upstream確認: mgba-emu/mgba tag0.10.2 src/gba/core.c _GBACoreResetがoutputBuffer設定時にrendererを接続する原本。Web検索後GitHub connectorで固定tag/blobを確認。外部コードを複製せず2resetだけ修復。ROM/save非追跡、merge/release/baseline切替なし。\n'
    for p in ('design/run_log.md','design/version_log.md'):
        with (ROOT/p).open('a') as f:f.write(note)
    for command in ([sys.executable,'-B','scripts/pr16_resume.py','check'],[sys.executable,'-B','scripts/validate_task_graph.py']):
        subprocess.run(command,cwd=ROOT,check=True)
    owned=c.owned()|{DRIVER,C}
    subprocess.run(['git','add','--',*sorted(owned)],cwd=ROOT,check=True)
    guard.START=head;guard.CODE={DRIVER,C};guard.OWNED=owned-{DRIVER,C};guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    out=ROOT/'.local/pr16-collection-observation';out.mkdir(parents=True);c.write(out/'verification.json',proof)


def execute():
    n,scope,c=install();old=c.load(ROOT/c.CP)
    proof=old['observation_repair']
    need(identity((ROOT/C).read_bytes())==proof['controller_after'] and identity((ROOT/DRIVER).read_bytes())==proof['driver_after'],'保存修復入力')
    normalized_driver((ROOT/DRIVER).read_bytes());normalized_render((ROOT/C).read_bytes())
    for p,b in proof['observation_source_bindings'].items():need(identity((ROOT/p).read_bytes())==b,'観測6unitのsource不変')
    from pr16_wiki_reconcile import fetch
    repair=fetch('actions/runs/'+str(proof['run_id']))
    need(repair['status']=='completed' and repair['conclusion']=='success' and repair['head_sha']==proof['input_head'],'観測修復終端')
    original_certificate=n.certificate
    def certified(legacy,repair,current):
        normalized=deepcopy(current);normalized[DRIVER]=identity(normalized_driver((ROOT/DRIVER).read_bytes()))
        result=original_certificate(legacy,repair,normalized)
        result['observation_repair']=proof;return result
    n.certificate=certified
    import pr16_collection_gift_step as step
    original_normalizer=step.normalized_controller
    step.normalized_controller=lambda raw:original_normalizer(normalized_render(raw))
    # headlessの3件は歴史的controller identityを保持。配布判定を変更しない描画差分だけ許容。
    original_pending=c.pending
    def scoped_pending(accepted,contracts):
        reviewed=deepcopy(contracts)
        for name,row in accepted.items():
            if row['contract']==contracts[name]:continue
            need(row['run_id']==36119380600 and name in proof['accepted_original_cases'],'旧controller適用範囲')
            need(row['contract']['controller']==proof['controller_before'] and contracts[name]['controller']==proof['controller_after'],'描画前後controller')
            reviewed[name]['controller']=row['contract']['controller']
        return original_pending(accepted,reviewed)
    c.pending=scoped_pending
    try:n.execute()
    finally:
        path=c.PROOF/'verification.json'
        if path.exists():
            v=c.load(path);v['observation_repair']=proof
            report={}
            for p in sorted(c.SHOTS.glob('*.ppm')):
                try:report[p.name]=dict(status='PASS_NONUNIFORM_PIXELS',**image_integrity(p.read_bytes()))
                except ValueError as e:report[p.name]=dict(status='INVALID_VISUAL_EVIDENCE',error=str(e),**identity(p.read_bytes()))
            c.write(c.PROOF/'screen-integrity.json',report)
            v['visual_evidence']=dict(previous_single_color_excluded=9,current_images=len(report),
                nonuniform_images=sum(x['status']=='PASS_NONUNIFORM_PIXELS' for x in report.values()),visual_semantics_accepted=False)
            need(report or not v['native_processes'],'実行した画像記録')
            v['proof_bindings']={p.name:identity(p.read_bytes()) for p in c.PROOF.iterdir() if p.is_file() and p.name!='verification.json'}
            c.write(path,v)
            if v['status'].startswith('PASS'):
                need(report and all(x['status']=='PASS_NONUNIFORM_PIXELS' for x in report.values()),'単色出力修復未完')


def main():
    need(len(sys.argv)==2,'prepare|execute|record|complete|guard|paths')
    action=sys.argv[1]
    if action=='prepare':prepare();return
    if action=='execute':execute();return
    n,scope,c=install()
    if action=='record':scope.record()
    elif action=='complete':n.complete()
    elif action=='guard':c.guard()
    elif action=='paths':print('\n'.join(sorted(c.owned())))
    else:raise ValueError('未知command')

if __name__=='__main__':main()
