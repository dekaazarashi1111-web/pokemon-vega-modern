#!/usr/bin/env python3
"""新Forest readerだけを測定・記録する。同branch通常push、原本は不変。"""
from __future__ import annotations
import contextlib
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import traceback
import unittest
import urllib.request
import pr16_forest_wallpaper_reader as m
import pr16_weather_bubble_receipt as parent
import pr16_wiki_r0_reconcile_actions as a
import pr16_wiki_r0_publish as publication

ROOT=Path(__file__).resolve().parents[1]
BASE='a31f8d09f9ee76c1ae17b69151c5b3c00c05ac3c'
TASK='USER-20261011-FOREST-ACTUAL-READER'
BRANCH='codex/modernization-followup-20260908'
STATE='content/modernization/pr16_wiki_first_execution_plan.json'
PREVIOUS='content/modernization/pr16_forest_wallpaper_asset_checkpoint.json'
PREVIOUS_BLOB='2dc8fd4bfde72eec7ddb35d6812798e192b75a67'
REPORT='content/modernization/pr16_forest_wallpaper_reader_checkpoint.json'
GUIDE='docs/PR16_FOREST_WALLPAPER_ASSET_JA.md'
LOGS={'design/run_log.md','design/version_log.md'}
CODE={'scripts/pr16_forest_wallpaper_reader.py','scripts/pr16_forest_wallpaper_reader_actions.py',
      'tests/test_pr16_forest_wallpaper_reader.py','.github/workflows/pr16-forest-wallpaper-reader.yml'}
OUTPUTS={REPORT,GUIDE,STATE,*LOGS}
WORK=ROOT/'.local/pr16-forest-reader'
PUBLIC=WORK/'public'
UPSTREAM='c75f352304d529f6ba92d4f74b9cf8b5c3810788'
SOURCE_BLOBS={
 'src/pokemon_storage_system_graphics.c':'046f82d9c6178d9457ee2e63c8952310fc96b93a',
 'include/pokemon_storage_system_internal.h':'9bd3434a2838349f922886f6874c52faa1014e8a',
 'src/new_menu_helpers.c':'08c032027cda2c34bf0dded37458adeb250aa553'}
PHASE='preflight'


def write(name,value):a.changed_write(name,m.encode(value) if type(value) is dict else value)

def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def public_layout():
    """固定公開型だけをARM向けにコンパイル。ROM/ゲーム本体は生成・実行しない。"""
    source=WORK/'public-upstream'
    subprocess.run(['git','init','-q',str(source)],check=True,capture_output=True)
    def git(*args):return subprocess.run(['git','-C',str(source),*args],check=True,capture_output=True).stdout
    git('remote','add','origin','https://github.com/pret/pokefirered.git')
    git('fetch','--depth=1','origin',UPSTREAM)
    git('checkout','--detach','FETCH_HEAD')
    m.need(git('rev-parse','HEAD').decode().strip()==UPSTREAM,'固定公開commit')
    bindings={}
    for name,expected in SOURCE_BLOBS.items():
        raw=(source/name).read_bytes();m.need(blob(raw)==expected,'公開source blob: '+name)
        bindings[name]={'git_blob':expected,**m.identity(raw)}
    helper=(source/'src/new_menu_helpers.c').read_text()
    for token in ('void *MallocAndDecompress(const void *src, u32 *size)',
                  'ptr = Alloc(*size);','LZ77UnCompWram(src, ptr);',
                  'CreateTask(TaskFreeBufAfterCopyingTileDataToVram, 0)',
                  'if (!WaitDma3Request(gTasks[taskId].data[0]))'):
        m.need(token in helper,'固定source意味: '+token)
    c=WORK/'layout.c';obj=WORK/'layout.o';out=WORK/'layout.bin';dep=WORK/'layout.d'
    values=['sizeof(struct PokemonStorageSystemData)']+['offsetof(struct PokemonStorageSystemData, '+n+')' for n in m.LAYOUT_FIELDS[1:]]
    c.write_text('#include "global.h"\n#include "gflib.h"\n#include "pokemon_storage_system_internal.h"\n#include <stddef.h>\n'
        'const unsigned int pr16_layout[] __attribute__((section(".pr16_layout"),used)) = {\n'+',\n'.join(values)+'\n};\n')
    command=['arm-none-eabi-gcc','-mcpu=arm7tdmi','-mthumb','-std=gnu11',
        '-I'+str(source/'include'),'-I'+str(source/'gflib'),'-I'+str(source),
        '-MMD','-MF',str(dep),'-c',str(c),'-o',str(obj)]
    compiled=subprocess.run(command,capture_output=True)
    if compiled.returncode:
        (WORK/'private-layout-errors.txt').write_bytes(compiled.stderr)
        raise ValueError('公開headerのARM layout compile失敗。private-layout-errorsへ保存')
    subprocess.run(['arm-none-eabi-objcopy','-j','.pr16_layout','-O','binary',str(obj),str(out)],check=True,capture_output=True)
    raw=out.read_bytes();m.need(len(raw)==4*len(m.LAYOUT_FIELDS),'layout全7整数')
    layout=dict(zip(m.LAYOUT_FIELDS,struct.unpack('<'+'I'*len(m.LAYOUT_FIELDS),raw)))
    m.validate_layout(layout)
    # -MMD依存だけを束縛。public clone全走査やprivate情報の収集はしない。
    dependencies={}
    for word in dep.read_text().replace('\\\n',' ').split():
        path=Path(word)
        if path.is_file() and path.is_relative_to(source):
            dependencies[path.relative_to(source).as_posix()]=m.identity(path.read_bytes())
    compiler=subprocess.run(['arm-none-eabi-gcc','-dumpfullversion'],check=True,capture_output=True).stdout.decode().strip()
    return layout,{'repository':'pret/pokefirered','commit':UPSTREAM,'source_bindings':bindings,
        'header_dependencies':dependencies,'compiler':'arm-none-eabi-gcc '+compiler,
        'layout':layout,'layout_identity':m.identity(raw),'probe_source_identity':m.identity(c.read_bytes()),
        'compiled_game_code':False,'game_native_processes':0}


def main():
    global PHASE
    m.need(os.environ.get('GITHUB_REPOSITORY')==a.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH
           and os.environ.get('GITHUB_RUN_ATTEMPT')=='1','same repo/branch first attempt')
    head=a.git('rev-parse','HEAD').decode().strip()
    m.need(head==os.environ['GITHUB_SHA'],'checkout event HEAD')
    observed=a.live(head)
    m.need(set(a.git('diff','--name-only',BASE,head).decode().splitlines())==CODE,'4 new scoped source files only')
    m.need(not (ROOT/REPORT).exists() and not WORK.exists(),'保存済みscopeを再測定しない')
    m.need(not a.git('status','--porcelain','--untracked-files=no').strip(),'tracked clean')
    nested=a.git('ls-files','--','scripts/AGENTS.md','tests/AGENTS.md','docs/AGENTS.md','design/AGENTS.md',
        'content/AGENTS.md','content/modernization/AGENTS.md','.github/AGENTS.md','.github/workflows/AGENTS.md')
    m.need(not nested.strip(),'追加AGENTSの確認が必要')
    WORK.mkdir(parents=True);PUBLIC.mkdir()
    state=parent.read((ROOT/STATE).read_bytes())
    lane=state['owner_execution_plan']['technical_lanes']['save_capacity']
    m.need(state['next_action']['id']=='SAVE_CAPACITY_FOREST_ACTUAL_ENTRY_READER'
        and lane['status']=='FOREST_ASSET_BOUND_ACTUAL_READER_PENDING'
        and state['owner_execution_plan']['wiki']['review_ready'] is True,'現在の固定nextのみ')
    original=(ROOT/PREVIOUS).read_bytes()
    m.need(blob(original)==PREVIOUS_BLOB,'旧asset checkpoint原本blob')
    previous=parent.read(original)
    inputs={PREVIOUS:m.identity(original),**previous['code_bindings'],**previous['dependency_bindings'],
            **previous['preserved_input_bindings']}
    before={name:((ROOT/name).stat().st_mtime_ns,m.identity((ROOT/name).read_bytes())) for name in inputs}
    m.need(all(meta==before[name][1] for name,meta in inputs.items()),'継承原本source/hash')
    inherited=publication.accepted_run(38066038086,'30a1edc5dc3cbbf0852a9ec955a1d77d32dc3e88',
        ['Forest whole asset, current table and LZ token verification','Run actions/upload-artifact@v4'])
    PHASE='new-tests'
    text=io.StringIO();suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_forest_wallpaper_reader.py')
    result=unittest.TextTestRunner(stream=text,verbosity=2).run(suite)
    (PUBLIC/'focused-tests.txt').write_text(text.getvalue())
    m.need(result.wasSuccessful() and result.testsRun==33 and not result.skipped,'33新規model境界試験')
    subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=ROOT,check=True,capture_output=True)
    PHASE='public-layout'
    layout,public_binding=public_layout()
    symbol=previous['public_symbol_source']
    with urllib.request.urlopen('https://raw.githubusercontent.com/'+symbol['repository']+'/'+symbol['commit']+'/'+symbol['path'],timeout=90) as response:
        raw_symbols=response.read(symbol['size']+1)
    m.need(blob(raw_symbols)==symbol['git_blob'],'公開JP symbol Git blob')
    sym=m.symbols(raw_symbols,symbol)
    PHASE='new-scope-reconstruction'
    import pr16_dex_hof_capacity_actions as reconstruction
    import pr16_dex_hof_donor as donor
    reconstruction.OUT=WORK/'candidate';reconstruction.OUT.mkdir()
    with (WORK/'private-reconstruction.log').open('w') as private_log,contextlib.redirect_stdout(private_log),contextlib.redirect_stderr(private_log):
        raw,current=reconstruction.reconstruct()
    m.need(m.identity(raw)==m.CANDIDATE and m.identity(raw)==current['candidate'],'新scope exact candidate')
    m.need(len(donor.bind_owners(raw,current))==115,'現115owner')
    # 保存済みasset/tupleのidentity照合のみ。PNG/compressor/旧reader/旧scanを再実行しない。
    for key in ('asset','consumed','table'):
        row=previous[key];start=row['address']-m.BASE
        m.need(m.identity(raw[start:start+row['size']])=={k:row[k] for k in ('size','sha256')},'継承bind: '+key)
    PHASE='actual-finite-reader'
    profiles=[]
    for offset in (0,1):
        for allocated in (True,False):
            profiles.append(m.compose(raw,sym,layout,allocated=allocated,offset=offset))
    m.need(before=={name:((ROOT/name).stat().st_mtime_ns,m.identity((ROOT/name).read_bytes())) for name in before},'全旧原本byte/mtime不変')
    PHASE='record-and-push'
    report={'schema_version':1,'status':'MEASURED_CONDITIONAL_FOREST_READER_FORMAL_RECEIPT_PENDING',
        'task':TASK,'source_head':head,'actions_run_id':int(os.environ['GITHUB_RUN_ID']),
        'actions_completion_confirmed':False,'previous_asset_actions':inherited,
        'previous_checkpoint':{'path':PREVIOUS,'git_blob':PREVIOUS_BLOB,**m.identity(original)},
        'candidate':dict(m.CANDIDATE),'claims':dict(m.CLAIMS),'conditions':dict(m.CONDITIONS),
        'source_binding':public_binding,'symbol_source':symbol,'symbols':sym,
        'profiles':profiles,'focused_tests':33,'new_profiles':len(profiles),'task_graph_passed':True,
        'rom_reconstructions':1,'classified':784,'unclassified':90,'donor_safe_bytes':0,
        'old_inputs_unchanged':True,'inherited_input_bindings':inputs,
        'code_bindings':{name:m.identity((ROOT/name).read_bytes()) for name in sorted(CODE)},
        'observed_head_checks':observed,'formal_receipt_created':False}
    modules={Path(module.__file__).resolve() for module in list(sys.modules.values())
        if getattr(module,'__file__',None) and str(Path(module.__file__).resolve()).startswith(str(ROOT)+'/scripts/')}
    report['dependency_bindings']={p.relative_to(ROOT).as_posix():m.identity(p.read_bytes()) for p in sorted(modules) if p.suffix=='.py'}
    goal='Forest新readerの成功run完了・原本hash・4profileの実call/stack/全4byte消費を読取専用で受領し、条件付き最小型1件だけを正式差分へ追加する。測定済みreader/ROM再構成/33試験と旧assetは再走しない。784/90・安全容量0は正式receiptまで維持。task/DMA/Freeと保存controllerは別gate。'
    report['next_ja']=goal
    write(REPORT,report)
    old=(ROOT/GUIDE).read_text()
    m.need('## 実readerの測定結果' not in old,'reader記録の重複拒否')
    old=old.replace('## 次の未完作業','## 全asset受入時の停止点（履歴）',1)
    counts='/'.join(str(p['instruction_count']) for p in profiles)
    addition=('\n## 実readerの測定結果\n\n'
        f'入力HEAD `{head}`、Actions `{report["actions_run_id"]}`。新33境界試験とtask graph PASS。前回asset run38066038086の全job/必須step成功を受領。\n\n'
        f'固定公開headerをARM向けにコンパイルしたlayoutと、実JP symbol/候補全SHAを束縛。オフセット0/1×確保成功/NULLの4条件を実Thumb {counts}命令で追跡。'
        'LoadWallpaperGfxの実table全3fieldと5引数、MallocAndDecompressのheader→1696byte確保要求、実malloc stack/保存レジスタ帰還を照合。'
        '成功側はSWI11仕様モデルが973byteを消費して1696byteを展開し、継承済み独立hashと一致。対象08397492全4byteを消費。NULL側はheaderのみでasset展開/heap書込なし、実loader帰還を確認。\n\n'
        'これは明示した正常同期ABIと非alias caller/heap状態に対する有限条件付き証明であり、実allocator/BIOS本体/描画/DMA/Freeのnative受入ではない。成功はCreateTask直前で止め、heap生存を記録する。\n\n'
        f'[新reader checkpoint](../{REPORT})。正式型受領は未完のため784分類/90未知/安全容量0を維持。旧asset/PNG/受入済みreaderの再走0、新scope候補再構成1、native0。\n\n'
        '## 次の未完作業\n\n'+goal+'\n')
    write(GUIDE,(old+addition).encode())
    lane.update(status='FOREST_READER_MEASURED_FORMAL_RECEIPT_PENDING',checkpoint_path=REPORT,next_ja=goal)
    state['next_action']={'id':'SAVE_CAPACITY_FOREST_READER_ACCEPTANCE_RECEIPT','goal_ja':goal,
        'read_paths':[GUIDE,REPORT,'scripts/pr16_forest_wallpaper_reader.py','docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md'],
        'done_ja':'成功Actions/原本/有限条件・厳格な受領検査に合格した場合だけ正式最小型差分を追加。安全容量/本番保存は未完を保つ。'}
    state['observed_head_checks']=observed
    state['recording']['status']='R0_READY_FOREST_READER_MEASURED_RECEIPT_PENDING'
    state['recording']['last_execution']={'task':TASK,'source_head':head,'actions_run_id':report['actions_run_id'],
        'actions_completion_confirmed':False,'previous_asset_actions':inherited,'focused_tests':33,
        'new_profiles':4,'task_graph_passed':True,'accepted_tests_rerun':0,'new_native_processes':0,'rom_reconstructions':1}
    write(STATE,state)
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    block=(f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / Forest実readerの有限条件付き検証\n'
        '- Version: forest-reader-v1\n- Status: DONE（新測定のみ。正式型受領/保存安全性は未完）\n'
        '- Summary: 実literal/table→heap helper→Malloc→SWI11を4条件で追跡。成功973byte消費/1696byte展開/全4byte被覆、NULL対照は展開なし。実stack/保存レジスタ帰還を束縛。\n'
        '- Files changed: 新reader/33試験/実行器/workflow/検証JSON、固定Forest引継ぎMD、現在JSON、両ログ。旧原本/Wiki R0/ROM/save/baselineは不変。\n'
        '- Verify: 新33 tests/task graph PASS。前回asset Actions完了成功、旧input byte/mtime不変。最終indexの新規private違反0と既存全体guard失敗を区別。非force競合/commit読戻しを実施。\n'
        '- Boundary: 正式784/90・donor安全容量0、native/旧試験/旧reader再走0、新scope候補再構成1。BIOS本体/allocator実装/task/DMA/Free/全story/製品完成を主張しない。\n'
        '- Commit: この記録を含む同branch単親通常commit。実SHAはGit履歴とActions resultで照合。\n'
        '- Network: 固定公開pret/pokefireredとJP symbol、既存許可済candidate復元、指定repo PR/ref/Actions GET、同branch非force push。\n')
    for name in LOGS:
        before_log=(ROOT/name).read_bytes();m.need(('- Task: '+TASK+' /').encode() not in before_log,'同task重複記録')
        write(name,before_log+block.encode())
    publication.final_index(BASE,CODE|OUTPUTS,REPORT)
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==head,'push前remote競合')
    for args in [('config','user.name','github-actions[bot]'),('config','user.email','41898282+github-actions[bot]@users.noreply.github.com'),
                 ('commit','-m',TASK+': Forest実readerの4条件を検証し正式受領待ちを記録'),('push','origin','HEAD:'+BRANCH)]:a.git(*args)
    pushed=a.git('rev-parse','HEAD').decode().strip()
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==pushed,'push後remote確認')
    for name in OUTPUTS:m.need(a.git('show','HEAD:'+name)==(ROOT/name).read_bytes(),'commit blob読戻し')
    (PUBLIC/'checkpoint.json').write_bytes((ROOT/REPORT).read_bytes())
    result={'status':'DONE','task':TASK,'commit':pushed,'source_head':head,'classified':784,'unclassified':90,
            'donor_safe_bytes':0,'focused_tests':33,'profiles':4,'rom_reconstructions':1,'native_processes':0}
    (PUBLIC/'result.json').write_bytes(m.encode(result))
    print(f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={pushed}')


if __name__=='__main__':
    try:main()
    except Exception as exc:
        # private復元ログ/byte列/環境変数を公開しない。新検証の停止点だけを保存。
        if PUBLIC.exists():
            safe={'status':'FAILED_NOT_ACCEPTED','phase':PHASE,'exception_type':type(exc).__name__,
                  'frames':[{'source':Path(frame.filename).name,'line':frame.lineno,'function':frame.name}
                            for frame in traceback.extract_tb(exc.__traceback__) if '/scripts/' in frame.filename]}
            if PHASE in ('actual-finite-reader','public-layout') and isinstance(exc,ValueError):safe['bounded_reason']=str(exc)
            (PUBLIC/'failure.json').write_bytes(m.encode(safe))
        print(f'RESULT=STOPPED TASK={TASK} VERIFY=FAIL COMMIT=- PHASE={PHASE}')
        sys.exit(1)
