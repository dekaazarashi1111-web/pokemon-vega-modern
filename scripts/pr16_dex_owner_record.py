#!/usr/bin/env python3
"""新規host実装だけを記録し、既存native/ROM/Saveを再実行しない。"""
from __future__ import annotations
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_namespace as namespace
from pr16_story_after_maori import need,identity,write
import pr16_story_live_probe as transport
import pr16_story_route_probe as publication
BASE='1c71d539e245d6a9fe83650b8a19ff3282e66c94'
TASK='USER-20261004-DEX-OWNER'
STATE='content/modernization/pr16_native_supply_resume_20260913.json'
DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
CP='content/modernization/pr16_dex_owner_checkpoint.json'
GUIDE='docs/PR16_DEX_OWNER_IMPLEMENTATION_JA.md'
UNIT='content/modernization/pr16_dex_owner_unit.json'
LOGS={'design/run_log.md','design/version_log.md'}
CODE={'scripts/pr16_dex_namespace.py','scripts/pr16_dex_alias_audit.py',
      'overlays/dex_owner/dex_owner.c','overlays/dex_owner/dex_owner.h',
      'tests/test_pr16_dex_owner.py',namespace.OUTPUT,
      'content/modernization/pr16_dex_alias_audit.json',
      'content/modernization/pr16_dex_storage_audit.json',
      'content/modernization/pr16_dex_consumer_audit.json','docs/PR16_DEX_CONSUMERS_JA.md',GUIDE,
      'scripts/pr16_dex_owner_record.py','.github/workflows/pr16-dex-owner-foundation.yml'}
OUT=ROOT/'.local/pr16-dex-owner-record'

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def bindings(paths):return {p:identity((ROOT/p).read_bytes())for p in sorted(paths)}
def current():
    need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'
         and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'
         and os.environ['GITHUB_RUN_ATTEMPT']=='1','single authorized branch attempt')
    pr=transport.api('pulls/16')
    need(pr['state']=='open' and pr['draft'] and not pr['merged']
         and pr['head']['sha']==os.environ['GITHUB_SHA'],'sole exact draft HEAD')
def source_guard():
    import pr16_learnset_runtime_record as guard
    current();guard.START=BASE;guard.CODE=CODE;guard.OWNED=set();guard.guard()
def record():
    from pr16_learnset_compact_record import publish_resume
    import pr16_resume
    current();need(not OUT.exists()and not(ROOT/CP).exists(),'one new codec checkpoint')
    OUT.mkdir();(OUT/'receipts').mkdir()
    state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings'])
    need(bindings(protected)==protected,'all accepted sources unchanged')
    need(state['pending_runs']==[],'no unclosed prior run')
    need((ROOT/namespace.OUTPUT).read_bytes()==namespace.serialized(namespace.build()),'exact namespace generation')
    test=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p',
                         'test_pr16_dex_owner.py','-v'],cwd=ROOT,capture_output=True,text=True)
    (OUT/'host.stdout.txt').write_text(test.stdout);(OUT/'host.stderr.txt').write_text(test.stderr)
    need(test.returncode==0 and test.stderr.count(' ... ok\n')==40 and '\nOK\n'in test.stderr,'all40 final focused host tests')
    unit=dict(schema_version=1,tests=40,passed=40,host_c_compiles=1,arm_compiles=0,native_processes=0,
              test_ids=[line.split(' ... ok')[0]for line in test.stderr.splitlines()if line.endswith(' ... ok')],
              source_bindings=bindings(CODE),scope='HOST_C_CODEC_AND_NAMESPACE_ONLY')
    write(ROOT/UNIT,unit)
    checkpoint=dict(schema_version=1,task=TASK,status='PASS_HOST_CODEC_NAMESPACE_RUNTIME_UNWIRED',
        source_head=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),
        source_bindings=bindings(CODE|{UNIT}),namespace_version=1,owner_count=1206,
        runtime_species_slots=1670,legacy_snapshot_bytes=208,serialized_bytes=522,
        host_tests=40,host_c_compiles=1,arm_compiles=0,native_processes=0,
        formal_story_save=101,rom_changed=False,save_changed=False,runtime_wired=False,
        repair_native_accepted=False,pc_lifetime_verified=False,milestone_reached=False,release_ready=False,
        unresolved=['PC/UI未保存RAM保持','全save mode/CRC bank fallback接続','全SID/official/nativeUI consumer接続',
                    '旧履歴の根拠付き昇格','候補normal Save/cold Continue限定native','シオウ回復milestone'],
        review_fixes=['namespace意味固定','C出力pointer/部分overlap拒否','監査出力hardlink拒否とatomic replace'])
    write(ROOT/CP,checkpoint)
    goal=('正式Save101は不変。図鑑修復の1206-owner stable namespaceと522byte MDX codecは40host試験済み、ROM未接続。'
          'pr16_dex_owner_checkpoint.jsonとPR16_DEX_OWNER_IMPLEMENTATION_JA.mdから再開し、まずRAM候補の未保存bitを'
          'PC/summary/bag/naming/図鑑往復で保持するlifetimeを実証し、退避ownerまたは保全経路を確定する。'
          'main logical13末尾companionの全save mode/CRC bank fallback、SID喪失前consumer、direct count/clear、'
          'memorial/Codex snapshotを署名付きlate-stageへ統合。旧52byteやVACQから曖昧なbitを複製しない。'
          '保存ABI/consumer限定native、通常Save/独立cold Continueを受入するまではtrainer戦闘を再開しない。'
          '受入後だけSave101未保存失敗区間からtrainer131/128/1065を進め、シオウPokecenter通常回復・Save・cold Continueへ。'
          '全雑魚戦checkpoint、未検証ROM基準切替、merge/releaseは禁止。')
    state['story_dex_owner']=dict(checkpoint=CP,guide=GUIDE,status=checkpoint['status'],
        source_head=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),
        host_tests=40,runtime_wired=False,repair_native_accepted=False,formal_story_save=101)
    state['next_action'].update(id='WIRE_DEX_OWNER_AFTER_RAM_LIFETIME_AUDIT',goal_ja=goal,
        read_paths=[GUIDE,CP,'content/modernization/pr16_dex_consumer_audit.json',
                    'content/modernization/pr16_dex_storage_audit.json','docs/PR16_DEX_SEEN_REPAIR_JA.md'])
    state['bp']['current_stop']='正式Save101保持。1206-owner namespace/522byte codecを40host試験。ROM未接続、PC保持と全consumer/save接続が未完。'
    state['bp']['next_step']=goal
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='図鑑ownerのhost実装checkpoint source。新native/ROM/Saveなし。正式進行Save101、trainer entry証拠は既存原本を継承。'
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['do_not_repeat'].append('図鑑owner namespace1206/slot1670と522byte codecのhost証拠を再利用。runtime未接続を修復済みにしない。旧bit、VACQ、別field破壊を根拠なしに昇格しない。PC未保存RAM保持と全save/consumer接続から続ける。')
    owned={STATE,DOC,CP,UNIT,*LOGS}
    state['source_bindings'].update(bindings(CODE|{CP,UNIT}));publish_resume(state);pr16_resume.validate(ROOT)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 図鑑owner保存codecの実装\n- Version: dex-owner-foundation-v1\n- Status: STOPPED（host基盤完成、ROM接続/native保存受入は未完）\n- Summary: 1670slotを既存1206ownerへstable-key結合。旧番号衝突277群/分裂52群を低開示metadataで確認。522byte codecは旧4鏡208byteを保持し、CRC/version/範囲/出力aliasを拒否。独立レビュー4件を修復。\n- Files changed: 専用namespace/codec/40試験/alias・保存・consumer監査/guide/checkpoint、固定resumeMD/JSON、両ログ。\n- Verify: final40 host試験PASS、host C compile1、namespace exact bytes、既受入source全hash保持。ARM0/native0/ROM変更0/Save変更0。\n- Next: {goal}\n- Commit: source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoGitHub読取と記録。ROM断片/raw hex/encoded name bytes/runtime/inputSaveの公開なし。一般CI既知QOL source不一致とStage79 cache区別は維持。\n'
    for path in LOGS:
        with(ROOT/path).open('a')as file:file.write(entry)
    need(bindings(protected)==protected,'accepted sources still unchanged')
    write(OUT/'owned.json',sorted(owned));write(OUT/'receipts/codec-record.json',checkpoint)
    git('add','--',*sorted(owned))
def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set()
    g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
    for path in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+path)==(ROOT/path).read_bytes(),'whole committed text bytes')
    print('RESULT=STOPPED TASK='+TASK+' VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
    if (OUT/'receipts').exists():publication.export_evidence(OUT/'receipts',ROOT/'public-dex-owner-receipts')
if __name__=='__main__':
    actions=dict(source_guard=source_guard,record=record,guard=guard,snapshot=snapshot,export=export)
    need(len(sys.argv)==2 and sys.argv[1]in actions,'bounded source-only record action');actions[sys.argv[1]]()
