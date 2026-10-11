#!/usr/bin/env python3
"""Forest新assetだけを復元候補へ照合し、private bytesを出さず同branchに記録する。"""
from __future__ import annotations
import contextlib
import ctypes
import datetime as dt
import io
import json
import os
from pathlib import Path
import subprocess
import unittest
import urllib.request
import pr16_forest_wallpaper_asset as m
import pr16_weather_bubble_receipt as parent
import pr16_wiki_r0_reconcile_actions as a
import pr16_wiki_r0_publish as publication

ROOT=Path(__file__).resolve().parents[1]
BASE='92c60863cc2ed2d28d5cb0834b113fc4661e621b'
TASK='USER-20261010-FOREST-WHOLE-ASSET'
STATE='content/modernization/pr16_wiki_first_execution_plan.json'
PREVIOUS='content/modernization/pr16_capacity_08397492_checkpoint.json'
REPORT='content/modernization/pr16_forest_wallpaper_asset_checkpoint.json'
GUIDE='docs/PR16_FOREST_WALLPAPER_ASSET_JA.md'
LOGS={'design/run_log.md','design/version_log.md'}
CODE={'scripts/pr16_forest_wallpaper_asset.py','scripts/pr16_forest_wallpaper_asset_actions.py',
 'tests/test_pr16_forest_wallpaper_asset.py','.github/workflows/pr16-forest-wallpaper-asset.yml'}
OUTPUTS={REPORT,GUIDE,STATE,*LOGS}
WORK=ROOT/'.local/pr16-forest-asset'
PUBLIC=WORK/'public'


def write(name,value):
    a.changed_write(name,m.encode(value) if type(value) is dict else value)


def download(repo,commit,path,limit):
    with urllib.request.urlopen('https://raw.githubusercontent.com/'+repo+'/'+commit+'/'+path,timeout=90) as response:
        raw=response.read(limit+1)
    m.need(len(raw)<=limit,'public source bounded: '+path)
    return raw


def compressor_crosscheck(raw,tiles,expected):
    """固定公開C compressorをhost shared libraryとして実行。ROM/ゲームコードなし。"""
    folder=WORK/'public-compressor';folder.mkdir()
    (folder/'lz.c').write_bytes(raw)
    (folder/'global.h').write_text('#include <stdio.h>\n#define FATAL_ERROR(...) do { fprintf(stderr, __VA_ARGS__); exit(2); } while (0)\n')
    (folder/'lz.h').write_text('/* Host-only declaration harness; implementation is pinned public lz.c. */\n')
    lib=folder/'liblz.so'
    process=subprocess.run(['cc','-shared','-fPIC','-std=c11','-O2','-Wall','-Wextra','-Werror',str(folder/'lz.c'),'-o',str(lib)],capture_output=True)
    m.need(process.returncode==0 and not process.stderr,'public C compressor compile')
    loaded=ctypes.CDLL(str(lib));loaded.LZCompress.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.POINTER(ctypes.c_int),ctypes.c_int]
    loaded.LZCompress.restype=ctypes.c_void_p
    buffer=ctypes.create_string_buffer(tiles);length=ctypes.c_int()
    address=loaded.LZCompress(buffer,len(tiles),ctypes.byref(length),2)
    m.need(address and length.value==len(expected),'public C compressor full size')
    try:result=ctypes.string_at(address,length.value)
    finally:
        libc=ctypes.CDLL(None);libc.free.argtypes=[ctypes.c_void_p];libc.free(address)
    m.need(result==expected,'independent Python and public C compressor byte equality')
    return {'status':'PASS_PINNED_PUBLIC_C_COMPRESSOR','private_rom_used':False,
            'game_native_processes':0,'compiled_game_code':False,'host_shared_library_calls':1,'result':m.identity(result)}


def run():
    m.need(os.environ.get('GITHUB_REPOSITORY')==a.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+parent.BRANCH
        and os.environ.get('GITHUB_RUN_ATTEMPT')=='1','same repo/branch first attempt')
    head=a.git('rev-parse','HEAD').decode().strip()
    m.need(head==os.environ['GITHUB_SHA'],'checkout exact event HEAD')
    observed=a.live(head)
    m.need(set(a.git('diff','--name-only',BASE,head).decode().splitlines())==CODE,'only four new scoped sources')
    m.need(not (ROOT/REPORT).exists() and not WORK.exists(),'completed/new scope is not rerun')
    m.need(not a.git('status','--porcelain','--untracked-files=no').strip(),'tracked clean')
    WORK.mkdir(parents=True);PUBLIC.mkdir()
    state=parent.read((ROOT/STATE).read_bytes())
    lane=state['owner_execution_plan']['technical_lanes']['save_capacity']
    m.need(state['next_action']['id']=='SAVE_CAPACITY_08397492_ASSET_AND_READER_PROOF'
        and state['owner_execution_plan']['wiki']['review_ready'] is True
        and lane['status']=='FRONTIER_BOUND_ASSET_READER_PROOF_PENDING','current authority and no flat lane')
    previous=parent.read((ROOT/PREVIOUS).read_bytes())
    completed=publication.accepted_run(previous['actions_run_id'],previous['source_head'],
        ['New frontier tests, saved parent and public symbol binding'])
    inputs={PREVIOUS:m.identity((ROOT/PREVIOUS).read_bytes()),**previous['code_bindings'],**previous['technical_parent_bindings']}
    before={name:((ROOT/name).stat().st_mtime_ns,m.identity((ROOT/name).read_bytes())) for name in inputs}
    m.need(all(m.exact(meta,before[name][1]) for name,meta in inputs.items()),'completed binding/technical originals')
    log=io.StringIO();suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_forest_wallpaper_asset.py')
    tests=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    m.need(tests.wasSuccessful() and tests.testsRun==34 and not tests.skipped,'34 new Forest tests only')
    (PUBLIC/'focused-tests.txt').write_text(log.getvalue())
    subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=ROOT,check=True,capture_output=True)
    sources={name:download('pret/pokefirered',m.COMMIT,name,100000) for name in m.BLOBS}
    public_bindings=m.source_bindings(sources)
    pixels,tiles,consumed,padded,tokens=m.independent(sources[m.PNG])
    from PIL import Image
    with Image.open(io.BytesIO(sources[m.PNG])) as image:
        m.need(image.mode=='P' and image.size==(64,56) and bytes(image.getdata())==pixels,'independent Pillow full pixel check')
    ccheck=compressor_crosscheck(sources['tools/gbagfx/lz.c'],tiles,padded)
    symbol=m.binding.SYMBOL_SOURCE
    table_source=download(symbol['repository'],symbol['commit'],symbol['path'],symbol['size'])
    rows=m.symbol_rows(table_source)
    # Restore evidence and reconstruct the exact candidate only for this NEW asset. No accepted reader/tests.
    audit=parent.restore_parent(ROOT)
    m.need(m.exact(m.identity(parent.previous.canonical(audit)),previous['parent_audit_identity']),'saved 784/90 full parent')
    m.binding.select_target(parent.frontier(audit))
    import pr16_dex_hof_capacity_actions as reconstruction
    import pr16_dex_hof_donor as donor
    reconstruction.OUT=WORK/'candidate';reconstruction.OUT.mkdir()
    with (WORK/'private-reconstruction.log').open('w') as private_log,contextlib.redirect_stdout(private_log),contextlib.redirect_stderr(private_log):
        raw,current=reconstruction.reconstruct()
    m.need(m.exact(m.identity(raw),current['candidate']) and len(donor.bind_owners(raw,current))==115,'exact current candidate and 115 owners')
    report=m.measure(raw,sources[m.PNG],rows)
    m.need(before=={name:((ROOT/name).stat().st_mtime_ns,m.identity((ROOT/name).read_bytes())) for name in before},'previous original bytes/mtimes unchanged')
    report.update(schema_version=1,task=TASK,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        actions_completion_confirmed=False,completed_previous_binding_actions=completed,focused_tests=34,
        task_graph_passed=True,rom_reconstructions=1,public_png_pixels_crosschecked=True,public_compressor=ccheck,
        public_sources=public_bindings,public_symbol_source=symbol,symbol_rows=rows,
        code_bindings={name:m.identity((ROOT/name).read_bytes()) for name in sorted(CODE)},
        preserved_input_bindings=inputs,parent_byte_mtime_unchanged=True,observed_head_checks=observed,
        reconstructed_current_owners=115,padded_extent_derived_from='fixed PNG + explicit 53 tiles build rule + compressor, never nearest-label difference')
    dependencies={Path(module.__file__).resolve() for module in list(__import__('sys').modules.values())
        if getattr(module,'__file__',None) and str(Path(module.__file__).resolve()).startswith(str(ROOT)+'/scripts/')}
    report['dependency_bindings']={p.relative_to(ROOT).as_posix():m.identity(p.read_bytes()) for p in sorted(dependencies) if p.suffix=='.py'}
    goal='Forest全asset976byte・実table先頭tuple・LZ消費973byte/展開1696byteは保存checkpointから継承し再測定しない。次はLoadWallpaperGfxの実literal/table選択→DecompressAndLoadBgGfxUsingHeap→LZ77境界を有限命令・caller状態・heap成功/失敗で結ぶ。成立するまで正式784/90・安全容量0を保持。全クリ/旧Bubble/Blastoiseの再走は禁止。'
    report['prior_attempts']=[{'run_id':38065787707,'source_head':'1184a59ed1b801f210ecf2170a84ea7798c56217','conclusion':'failure','rom_reconstructions':0,'completion_commit_created':False,'reason_ja':'保存親のcanonical serializerをreceipt.previous.canonicalへ修正。期待SHAは据置き。依存APIの回帰試験1件を追加。'}]
    report['next_ja']=goal
    write(REPORT,report)
    guide=('# Forest壁紙：全asset・実table・LZ tokenの照合\n\n'
        '**全assetの限定検証は完了。実entryからheap/BIOSへ至る条件付きreaderと正式型受入は未完です。**\n\n'
        f'入力HEAD `{head}`、Actions `{report["actions_run_id"]}`、新34境界試験とtask graph PASS。先行bindingのActionsはcompleted/successを照合済み。\n\n'
        '公開PNGは64×56で56tile相当ですが、固定ビルドルールは`-num_tiles 53`です。最後の空3tileを除いた1696byteから生成し、消費973byte、整列込み976byteを確定しました。Pillow全pixel照合と固定公開C compressorでも同一結果です。\n\n'
        '現候補0641af70…を新scopeのためだけに再構成し、全32MiB SHAと115ownerを照合しました。0x08397188の全976byte、sWallpapers先頭の12byte tuple、保存hit0x08397492の4byteが一致しました。対象はLZ参照2byte・literal1byte・flags1byteで、整列paddingではありません。ROM/PNG/生byte列は公開せずhashとtoken型だけを記録します。\n\n'
        f'[機械可読checkpoint](../{REPORT})に全source/依存/親のidentity、symbol行、tokenごとの範囲と展開位置を保存しました。\n\n'
        '## 次の未完作業\n\n'+goal+'\n\n'
        'このtoken parserはBIOSやゲームentryの実行ではありません。sourceでcallがあることとtable一致だけからreader成立へ昇格しません。controller6528byte配置、同期heap寿命、保存writer/loaderと局所Save/fresh Continueは別gateです。所有者調整承認0、正式ROM/Save101・baseline不変、merge/releaseなし。\n')
    write(GUIDE,guide.encode())
    lane['status']='FOREST_ASSET_BOUND_ACTUAL_READER_PENDING';lane['checkpoint_path']=REPORT
    lane['next_ja']=goal
    state['next_action']={'id':'SAVE_CAPACITY_FOREST_ACTUAL_ENTRY_READER','goal_ja':goal,
        'read_paths':[GUIDE,REPORT,'scripts/pr16_forest_wallpaper_asset.py','docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md'],
        'done_ja':'実entry/literal/table/heap/LZ境界の全4byte消費を証明した場合だけ最小型を受入。未証明のまま安全容量や本番保存を有効化しない。'}
    state['observed_head_checks']=observed
    state['recording']['status']='R0_READY_FOREST_ASSET_BOUND_ACTUAL_READER_PENDING'
    state['recording']['last_execution']={'task':TASK,'source_head':head,'actions_run_id':report['actions_run_id'],
        'actions_completion_confirmed':False,'completed_previous_binding_actions':completed,'focused_tests':34,
        'task_graph_passed':True,'accepted_tests_rerun':0,'new_native_processes':0,'rom_reconstructions':1}
    write(STATE,state)
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    block=(f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / Forest全assetと実table\n'
        '- Version: forest-whole-asset-v1\n- Status: DONE（全asset限定検証。実entry/heap/BIOS型受入は未完）\n'
        '- Summary: 公開PNGと53tile専用ruleから1696byteを独立生成。LZ消費973/整列976をPillowと公開Cで交差検証し、現0641候補全SHA/115ownerと全asset/table/4byte token一致。\n'
        '- Files changed: 新Forestモデル/34試験/実行器/workflow/MD/JSON、現行状態JSON、両ログ。旧証拠/原本/baselineは不変。\n'
        '- Verify: 新34 tests/task graph、前binding completed成功、全parent byte/mtime不変、最終index/非force競合/commit読戻し。旧試験/旧reader/ゲームnative各0、新scope ROM復元1。\n'
        '- Boundary: 784分類90未知・安全容量0を保持。table近傍やtoken parseを実entry/heap/BIOS実行と混同しない。全体CI/private guardの既存失敗をPASSへ変えない。\n'
        '- Commit: この記録を含む同branch単親commit。実SHAはGit履歴とActions resultから照合。\n'
        '- Network: 固定公開source、既存許可済private候補再構成、指定repo PR/ref/Actions GETと同branch非force push。\n')
    for name in LOGS:
        old=(ROOT/name).read_bytes();m.need(('- Task: '+TASK+' /').encode() not in old,'task log unique')
        write(name,old+block.encode())
    publication.final_index(BASE,CODE|OUTPUTS,REPORT)
    m.need(a.git('ls-remote','origin','refs/heads/'+parent.BRANCH).decode().split()[0]==head,'remote unchanged')
    for args in [('config','user.name','github-actions[bot]'),('config','user.email','41898282+github-actions[bot]@users.noreply.github.com'),
        ('commit','-m',TASK+': 全assetとLZ消費を検証し実reader未完を記録'),('push','origin','HEAD:'+parent.BRANCH)]:a.git(*args)
    pushed=a.git('rev-parse','HEAD').decode().strip()
    m.need(a.git('ls-remote','origin','refs/heads/'+parent.BRANCH).decode().split()[0]==pushed,'remote readback')
    for name in OUTPUTS:m.need(a.git('show','HEAD:'+name)==(ROOT/name).read_bytes(),'commit file readback')
    result={'status':'DONE','commit':pushed,'source_head':head,'task':TASK,'classified':784,'unclassified':90,'donor_safe_bytes':0}
    (PUBLIC/'result.json').write_bytes(m.encode(result));print(json.dumps(result))


if __name__=='__main__':run()
