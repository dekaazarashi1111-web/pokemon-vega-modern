#!/usr/bin/env python3
"""固定HEADの誤ったNPC検査だけをBG契約へ修復し、非native証跡を保存。"""
from __future__ import annotations
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
TASK='USER-20260925-COLLECTION-BG-REPAIR'
CODE='scripts/pr16_collection_gifts.py'
SCOPE='scripts/pr16_collection_gift_scope.py'
TEST='tests/test_pr16_collection_gifts.py'
C='tools/mgba_pr16_collection_gifts.c'
SELF='scripts/pr16_collection_bg_prepare.py'
BG='scripts/pr16_collection_gift_bg.py'
BGTEST='tests/test_pr16_collection_gift_bg.py'
WF='.github/workflows/pr16-supply-followup-20260925.yml'
EXPECTED={CODE:'3ea4ad760aa89f3dc1d95648a10d000f55097e4ae245265e1a7014ce9927bafb',
 SCOPE:'10ceaace4d5608591d32a60b72e40d4b0f9824d9cc08cd976cb7e2b095cd732c',
 TEST:'0b2d4f9e1da684bbb0108fe83fe7fb3010f9d76e420c90f8acb019aa1215078f',
 C:'130935e36f5f91642eaf481a5731a2953971436299077d82863ec76ba9740317'}

def need(ok,message):
    if not ok:raise ValueError(message)

def identity(raw):return dict(sha256=hashlib.sha256(raw).hexdigest(),size=len(raw))

def once(text,old,new):
    need(text.count(old)==1,'一意の修復箇所: '+old[:80]);return text.replace(old,new)

def patch():
    src={p:(ROOT/p).read_text() for p in EXPECTED}
    for p,sha in EXPECTED.items():need(identity(src[p].encode())['sha256']==sha,'固定入力source '+p)
    text=src[CODE]
    start=text.index('def geometry(rom, config):');end=text.index('\n\ndef header(',start)
    text=text[:start]+'''def geometry(rom, config):
    # Collection SupplyはNPCではなく通常A入力のBG eventを追加する。
    from pr16_collection_gift_bg import geometry as bg_geometry
    return bg_geometry(rom, config)
'''+text[end:]
    text=once(text,'CODE = {SELF, TEST, C, WF}',"CODE = {SELF, TEST, C, WF, 'scripts/pr16_collection_gift_bg.py', 'tests/test_pr16_collection_gift_bg.py'}")
    text=once(text,'for p in (TEST,SELF,C)',"for p in (TEST,SELF,C,'scripts/pr16_collection_gift_bg.py','tests/test_pr16_collection_gift_bg.py')")
    text=once(text,"'tests.test_pr16_collection_gifts','-v'","'tests.test_pr16_collection_gifts','tests.test_pr16_collection_gift_bg','-v'")
    text=once(text,'cases=vectors(model,rows,pp);geo=geometry(rom,load(ROOT/CONFIG))',"cases=vectors(model,rows,pp);v['declared_cases']=[case['name'] for case in cases]\n        geo=geometry(rom,load(ROOT/CONFIG))")
    src[CODE]=text
    text=src[C]
    text=once(text,'/* Issue19 Collection gifts: actual NPC/menu inputs, never a TestGift call.', '/* Issue19 Collection gifts: actual BG/menu inputs, never a TestGift call.')
    text=once(text,'    cf_press(c,QOL_KEY_UP,30U);b_position(c,CF_GROUP,CF_NUMBER,CF_X,CF_Y);\n','')
    text=once(text,'(void)call_preserving(c,0x09220861U,CF_GROUP,CF_NUMBER,CF_X,CF_Y);run_key_frames(c,0U,900U);\n    b_position(c,CF_GROUP,CF_NUMBER,CF_X,CF_Y);cf_fixture_owner(c);',
'''(void)call_preserving(c,0x09220861U,CF_GROUP,CF_NUMBER,CF_X,CF_Y+1U);run_key_frames(c,0U,900U);
    b_position(c,CF_GROUP,CF_NUMBER,CF_X,CF_Y+1U);
    /* BGは歩行可能。初期fixture区間で1マス上へ移動し、その後はAだけ。 */
    cf_press(c,QOL_KEY_UP,30U);b_position(c,CF_GROUP,CF_NUMBER,CF_X,CF_Y);cf_fixture_owner(c);''')
    src[C]=text
    text=src[TEST]
    start=text.index('    def test_geometry_uses_actual_object_and_native_script(self):')
    end=text.index('    def test_controller_barriers_and_no_testgift_execution(self):',start)
    text=text[:start]+'''    def test_geometry_uses_actual_bg_and_native_script(self):
        from tests.test_pr16_collection_gift_bg import fixture
        rom,config=fixture();geo=c.geometry(rom,config)
        self.assertEqual((geo['event_kind'],geo['x'],geo['y']),('BG_NORMAL_FIELD_A',21,4))
        rom[0x600]=0
        with self.assertRaises(ValueError):c.geometry(rom,config)
'''+text[end:]
    src[TEST]=text
    text=src[SCOPE]
    text=once(text,"pending=[n for n in v.get('contracts',{}) if n not in good]","pending=[n for n in v.get('declared_cases',v.get('contracts',{})) if n not in good]")
    text=text.replace('実NPC','実BG受付').replace('初期party、開始場所、全unlock','初期party、開始場所と向き、全unlock')
    # legacy scope/key名は旧失敗原本とのschema互換用。新しいgeometryがBGを明示する。
    text=once(text,'## 範囲と保留\\n\\n固定form2','## 範囲と保留\\n\\n受付はNPC/objectではなく通常A入力のBGイベント。legacy `COLLECTION_NPC_INITIAL_MOVES_SAVE_CONTINUE` / `npc_script` はschema互換名でありNPC同定を意味しない。\\n\\n固定form2')
    src[SCOPE]=text
    for p,text in src.items():(ROOT/p).write_text(text)
    return src


def execute():
    head=os.environ['GITHUB_SHA'];run=int(os.environ['GITHUB_RUN_ID'])
    need(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==head,'exact HEAD')
    need(not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),'clean source')
    changed=patch()
    prefix='tests.test_pr16_collection_gifts.CollectionGiftsTests.'
    tests=['tests.test_pr16_collection_gift_bg']+[prefix+n for n in (
      'test_geometry_uses_actual_bg_and_native_script','test_controller_barriers_and_no_testgift_execution',
      'test_header_only_original_vectors','test_synthetic_fixed_record_consistent','test_synthetic_research_record_consistent')]
    result=subprocess.run([sys.executable,'-B','-m','unittest',*tests,'-v'],cwd=ROOT,capture_output=True)
    sys.stdout.buffer.write(result.stdout);sys.stderr.buffer.write(result.stderr)
    need(result.returncode==0 and b'Ran 7 tests' in result.stderr and b'\nOK\n' in result.stderr,'BG影響7試験/skip0')
    import pr16_collection_gifts as c
    import pr16_learnset_runtime_record as guard
    from pr16_learnset_compact_record import publish_resume
    prior=c.load(ROOT/c.CP)
    need(prior['run_id']==36111746469 and prior['source_head']=='194670bade3bcb584e651db301c09ba11c7eeb29'
         and not prior['accepted'] and prior['native_processes']==0,'旧停止点不変')
    url='https://api.github.com/repos/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/36111746469'
    request=urllib.request.Request(url,headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],'Accept':'application/vnd.github+json'})
    with urllib.request.urlopen(request,timeout=60) as response:raw=json.load(response)
    need(raw['status']=='completed' and raw['conclusion']=='failure' and raw['head_sha']==prior['source_head'],'前run終端原本')
    terminal={k:raw[k] for k in ('id','head_sha','status','conclusion','path')}
    dest=ROOT/c.EVIDENCE/str(run);dest.mkdir(parents=True)
    proof=dict(schema_version=1,task=TASK,status='PASS_HOST_BG_REPAIR_NATIVE_PENDING',input_head=head,run_id=run,
      predecessor=terminal,prior_native_processes=0,accepted_case_reruns=0,new_native_processes=0,host_compiles=0,arm_compiles=0,
      rom_changes=0,unit_tests=7,unit_skips=0,geometry_negative_subcases=16,modified_source_after_input_head=True,
      source_before=EXPECTED,source_after={p:identity((ROOT/p).read_bytes()) for p in sorted(set(changed)|{BG,BGTEST,SELF,WF})},
      candidate=prior['candidate'],issue19_complete=False,release_ready=False,active_baseline_changed=False)
    c.write(dest/'bg-repair.json',proof);(dest/'bg-repair-unit.stderr.txt').write_bytes(result.stderr)
    state=c.load(ROOT/c.m.STATE)
    state['learnset_collection_bg_repair']=dict(path=(dest/'bg-repair.json').relative_to(ROOT).as_posix(),**proof)
    nextstep='CollectionのBG受付契約と初期接近を修復済み。固定候補b7790902を再利用し、未受入の学習owner17配布だけnative実行。1281は非学習ownerのまま保留。旧失敗run/受入原本は改作・再実行しない。'
    state['bp']['current_stop']='Issue19: Collection BG検出/接近の影響7試験PASS。nativeは0/17のまま未実行。'
    state['bp']['next_step']=nextstep
    state['next_action']=dict(state['next_action'],id='COLLECTION_GIFTS_BG_NATIVE',goal_ja=nextstep)
    for p in set(changed)|{BG,BGTEST,SELF,WF}:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    note=f'\n## {now}\n- Timestamp: {now}\n- Task: {TASK} / Collection BG受付契約の修復\n- Version: collection-bg-contract-v1\n- Status: DONE（host修復限定、native配布0/17は未完）\n- Summary: 24byte NPC探索を12byte BG探索へ修正。通常A種別/host script/高度/接近2マス/他event衝突を検査。歩行可能BGへ突入せず、fixture区間で向きを確定しguard後はAのみ。前run36111746469 completed/failureを原本のまま照合。\n- Files changed: BG検出器・拒否試験、driver/C/影響unit/scope説明、固定引継ぎMD/JSON、BG修復証跡、両ログ。\n- Verify: 影響7unit PASS/skip0（BG拒否16変異含む）、native/host compile/ARM/ROM変更0。受入済みnative再実行0。resume/task graph/final index scoped private guardをcommit前検査。\n- Commit: この記録とsource変更を同branchへ非force commit/push。自己SHAはreflected-head.txt/remoteで照合。\n- Network: GitHub固定source/保存source artifact/前run終端のみ。ROM/saveを転送・追跡しない。merge/release/baseline切替なし。\n'
    for path in ('design/run_log.md','design/version_log.md'):
        with (ROOT/path).open('a') as f:f.write(note)
    subprocess.run([sys.executable,'-B','scripts/pr16_resume.py','check'],cwd=ROOT,check=True)
    subprocess.run([sys.executable,'-B','scripts/validate_task_graph.py'],cwd=ROOT,check=True)
    owned=set(changed)|{c.m.STATE,c.m.DOC,'design/run_log.md','design/version_log.md'}|{p.relative_to(ROOT).as_posix() for p in dest.iterdir()}
    subprocess.run(['git','add','--',*sorted(owned)],cwd=ROOT,check=True)
    guard.START=head;guard.CODE=set(changed);guard.OWNED=owned-set(changed);guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    out=ROOT/'.local/pr16-collection-bg-repair';out.mkdir(parents=True)
    (out/'verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':execute()
