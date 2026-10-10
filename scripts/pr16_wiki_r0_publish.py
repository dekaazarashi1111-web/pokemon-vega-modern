#!/usr/bin/env python3
"""R0の有限な生成/提示受領。検証済み生成の無変更再走と自己SHA追記ループを禁止する。"""
from __future__ import annotations
import argparse
from collections import Counter
import datetime as dt
import json
import os
import subprocess
import zipfile
import pr16_wiki_r0_build as b
import pr16_wiki_r0_reconcile_actions as a

r=b.r
START='7e24575a5891636630ae6bece0f52fd3ad9d4816'
VERIFY='content/modernization/pr16_wiki_r0_verification.json'
PRESENTATION='content/modernization/pr16_wiki_r0_presentation.json'
RECEIPT='content/modernization/pr16_wiki_r0_receipt.json'
ENTRY='docs/wiki/README.md'
LOGS={'design/run_log.md','design/version_log.md'}
WORK=r.ROOT/'.local/pr16-wiki-r0-build'
RECEIPT_TASK='USER-20261010-WIKI-R0-RECEIPT'
RECONCILE_RUN=38051218790
RECONCILE_HEAD='0534d2d187bbb04ef4fe1b7b681d3f5930ab7fd7'


def write(name,raw):a.changed_write(name,raw)

def stamp():return dt.datetime.now(dt.timezone.utc).isoformat()

def run(*args):return subprocess.run(args,cwd=r.ROOT,check=True)


def accepted_run(run_id,source_head,required_steps):
    value=a.fetch('actions/runs/'+str(run_id))
    r.need(value['head_sha']==source_head and value['head_branch']==r.BRANCH and value['status']=='completed' and value['conclusion']=='success','原本Actions未完/identity不一致')
    jobs=a.fetch('actions/runs/'+str(run_id)+'/jobs?filter=latest&per_page=100')
    r.need(jobs['total_count']==len(jobs['jobs']) and all(j['status']=='completed' and j['conclusion']=='success' for j in jobs['jobs']),'job原本未成功/未取得')
    steps={s['name']:s for j in jobs['jobs'] for s in j['steps']}
    r.need(all(name in steps and steps[name]['status']=='completed' and steps[name]['conclusion']=='success' for name in required_steps),'必須stepが未成功/skip')
    return {'id':run_id,'source_head':source_head,'status':'completed','conclusion':'success','required_steps':required_steps,'observed_at':stamp()}


def append_logs(task,summary,verify):
    now=stamp()
    block=(f'\n## {now}\n- Timestamp: {now}\n- Task: {task} / 固定Wiki R0\n- Version: wiki-r0-6e88a021\n- Status: DONE\n'
           f'- Summary: {summary}\n- Files changed: R0専用生成/検証と固定引継ぎMD/JSON、Wiki入口、両ログ。旧Wiki/ROM/Save101/baselineは不変。\n'
           f'- Verify: {verify}\n- Commit: この記録を含む同branchの単親通常commit。実SHAはActions resultとGit履歴から照合する。\n'
           '- Network: GitHubの指定PR/ref/受入済みActionsのGETと同branchへの非force pushのみ。元資料の再採取なし。\n')
    for name in LOGS:
        before=r.read(r.ROOT,name);r.need(('- Task: '+task+' /').encode() not in before,'同task記録済み。再走禁止')
        write(name,before+block.encode())


def guide(index,presented=False):
    text='# Wiki R0 入力監査と継続点\n\n'
    text+=('**固定R0を公開・提示し、レビュー可能な状態を記録済みです。**' if presented else '**R0全ページと検証を生成済み。リモート公開後、実際の提示とActions完了を受領する段階です。**')+'\n\n'
    text+='[固定Wiki R0](wiki/r0-6e88a021/README.md) / [ベガ横比較](wiki/r0-6e88a021/VEGA_BALANCE_INDEX.md) / [現在の作業状態](../'+r.STATE+')。\n\n'
    text+='候補SHA `'+r.NEW_SHA+'` / 33554432 bytes / CRC32 `00F31AF7`。入力HEAD `'+index['source_head']+'`。意味hash `'+index['semantic_sha256']+'`。\n\n'
    text+='[全入力・生成hash](wiki/r0-6e88a021/data/index.json) / [数値系譜](../'+r.REPORT+') / [R0検証](../'+VERIFY+')。数値は受入済み5段・7013範囲の非変更を継承、現役習得128389経路/109659条件だけを結合。持越し35211行・条件付き繁殖5行を無条件の直接付与にしません。\n\n'
    text+='ベガ206行、全1671種族/フォーム、1063技/318特性の逆引き、1044道具、76メガ、34Gmax登録、31専用Z、資源/供給/効果の未確認を掲載。新native/ROM再構成/旧受入再走0。\n\n'
    if presented:
        text+='## 次の未完作業\n\n固定JSONの保存capacity laneへ戻り、保存済みWeather Bubbleの784分類/90未知/安全容量0から次の0x08397492と必要な保存controller容量・接続を有限scopeで進める。これは最後の未知1件ではありません。所有者案待ちだけで止めず、成功原本を再採取しない。\n'
    else:
        text+='## 次の未完作業\n\n公開commitの固定R0入口を会話で提示し、presentation JSONにそのcommit/意味hash/生成runを記録する。同じworkflowのreceipt分岐が生成を再走せず、Actions完了・公開tree不変・提示を束縛して固定状態を更新する。\n'
    text+='\n全クリ走破は対象外（PASSではない）。保存安全性・局所Save/fresh Continue・容量移管・CI整理は未完。所有者調整承認0、release未完、merge/baseline切替なし。旧native resume/checkpointは保留原本のまま保全する。\n'
    return text.encode()


def set_guard_result(path,proof):
    state=r.load(r.read(r.ROOT,r.STATE));state['recording']['full_index_private_guard_executed']=True
    state['recording']['last_execution']['full_index_private_guard']=proof
    write(r.STATE,r.encode(state))
    value=r.load(r.read(r.ROOT,path));value['full_index_private_guard']=proof
    value['scoped_final_index_guard']={'status':'PASS','new_private_violations':0,'historical_guard_pass_claimed':False}
    write(path,r.encode(value))


def final_index(base,allowed,report):
    run('git','add','--',*sorted(allowed))
    full=subprocess.run(['python3','-B','scripts/guard_private_files.py'],cwd=r.ROOT,capture_output=True)
    result={'executed':True,'passed':full.returncode==0,'exit_code':full.returncode,'historical_violations_not_rewritten':True,'raw_private_log_published':False}
    set_guard_result(report,result);run('git','add','--',r.STATE,report)
    import guard_private_files as private
    actual={n for n in a.git('diff','--cached','--name-only','-z',base).decode().split('\0') if n}
    r.need(actual==allowed,'最終index範囲不一致: '+str(actual^allowed))
    for name in sorted(actual):
        raw=a.git('show',':'+name);raw.decode();r.need(b'\0' not in raw,'binary追加禁止')
        before=subprocess.run(['git','show',base+':'+name],cwd=r.ROOT,capture_output=True).stdout
        def violations(value):
            lines=value.decode(errors='replace').splitlines()
            return Counter(lines[n-1] for n in private.document_user_path_lines(value))
        r.need(not violations(raw)-violations(before),'新しいprivate記載: '+name)
        if name in LOGS:r.need(raw.startswith(before),'append-only違反')
    run('git','merge-base','--is-ancestor',base,'HEAD');run('git','diff','--cached','--check',base)
    return {'status':'PASS_SCOPED_FINAL_INDEX','paths':len(actual),'full_index_private_guard':result}


def publish(task,source_head):
    live=a.git('ls-remote','origin','refs/heads/'+r.BRANCH).decode().split()[0]
    r.need(live==source_head,'push直前HEAD競合')
    run('git','config','user.name','github-actions[bot]');run('git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    run('git','commit','-m',task+': 固定R0の検証結果と次の未完作業を記録')
    run('git','push','origin','HEAD:'+r.BRANCH)
    head=a.git('rev-parse','HEAD').decode().strip()
    r.need(a.git('ls-remote','origin','refs/heads/'+r.BRANCH).decode().split()[0]==head,'push後HEAD不一致')
    (WORK/'proof/result.txt').write_text(f'RESULT=DONE TASK={task} VERIFY=PASS COMMIT={head}\n')
    return head


def snapshot(names):
    with zipfile.ZipFile(WORK/'context.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(set(names)-LOGS):
            if (r.ROOT/name).is_file():archive.writestr(name,r.read(r.ROOT,name))


def build(source_head,tests):
    r.need(tests>0,'新しい試験件数が必要');observed=a.live(source_head)
    nested=a.git('ls-files','--','docs/AGENTS.md','docs/wiki/AGENTS.md','docs/wiki/r0-6e88a021/AGENTS.md','scripts/AGENTS.md','tests/AGENTS.md','.github/AGENTS.md','.github/workflows/AGENTS.md','content/AGENTS.md','content/modernization/AGENTS.md','design/AGENTS.md').decode().strip()
    r.need(not nested,'追加AGENTSの読取りが必要: '+nested)
    r.need(not (r.ROOT/b.OUT).exists(),'固定R0は既に存在。無変更再生成・上書きを開始しない')
    inherited=accepted_run(RECONCILE_RUN,RECONCILE_HEAD,['新しい系譜境界35試験とtask graph','受入済みlinkを読取り数値と現registryを照合して記録','最終indexと原本保護を確認','同branchへ単親commitと非force push'])
    files,index,links=b.generate(r.ROOT,source_head);b.write_outputs(r.ROOT,files)
    proof=b.check(r.ROOT)
    proof.update(source_head=source_head,task=b.TASK,focused_tests=tests,accepted_tests_rerun=0,new_native_processes=0,rom_reconstructions=0,reconciliation_actions=inherited,actions_run_id=int(os.environ['GITHUB_RUN_ID']),actions_completion_confirmed=False,task_graph_passed=True)
    write(VERIFY,r.encode(proof))
    state=r.load(r.read(r.ROOT,r.STATE));r.need(state['decision_id']=='OWNER-20261010-WIKI-FIRST' and not state['owner_execution_plan']['wiki']['review_ready'],'方針/状態不一致')
    wiki=state['owner_execution_plan']['wiki'];wiki.update(status='GENERATED_VERIFIED_PUBLICATION_RECEIPT_PENDING',source_head=source_head,candidate=index['candidate'],entry_path=b.OUT+'/README.md',input_manifest_path=b.INDEX,verification_evidence_path=VERIFY,semantic_sha256=index['semantic_sha256'],tree_sha256=index['tree_sha256'],published_commit=None,review_ready=False,presented_to_owner=False,
        limitations=['数値は範囲非変更の継承。全native/自然供給/保存統合の受入ではない。','Gmax登録34件の個別資源body/発動/終了は未監査。','容量784分類/90未知/安全容量0。全クリ対象外、所有者調整承認0。'])
    for key in wiki['completion_gates']:wiki['completion_gates'][key]=(key!='published_and_presented')
    state['next_action']={'id':'WIKI_R0_PRESENT_AND_BIND_COMPLETED_ACTIONS','goal_ja':'公開した固定R0を会話で提示し、生成run完了と公開commitをreceiptへ束縛する。受入済み生成は再走しない。','read_paths':[r.GUIDE,VERIFY,b.INDEX],'done_ja':'提示receiptを記録し、次の保存容量laneへ継続点を移す。'}
    state['observed_head_checks']=observed
    state['recording']['last_execution']={'task':b.TASK,'source_head':source_head,'focused_tests':tests,'accepted_tests_rerun':0,'new_native_processes':0,'rom_reconstructions':0,'read_only_check_passed':True,'task_graph_passed':True,'actions_run_id':int(os.environ['GITHUB_RUN_ID']),'actions_completion_confirmed':False}
    state['recording'].update(status='R0_RENDER_VERIFIED_RECEIPT_PENDING',wiki_generated=True,project_task_graph_check_executed=True,mode='SCOPED_R0_BUILD_AND_NONFORCE_PUSH')
    write(r.STATE,r.encode(state));write(r.GUIDE,guide(index))
    write(ENTRY,('# 開発Wiki\n\n[固定調整基準Wiki R0](r0-6e88a021/README.md) / [ベガ横比較](r0-6e88a021/VEGA_BALANCE_INDEX.md)。候補 `'+r.NEW_SHA+'`、R0の数値と現役習得を結合。配布/保存統合の完成宣言ではありません。\n\n[旧P08履歴](p08-candidate-46487d98/README.md) / [Issue19習得履歴](issue19-candidate-6e88a021/README.md) / [Stage61固定履歴](stage61/README.md)。旧Wikiは改作していません。\n').encode())
    append_logs(b.TASK,f'R0 {len(files)} textファイル、{links}内部リンク、全128389経路/109659条件、ベガ206行/1671種族/1063技/318特性/1044道具/76メガ/34Gmax/31専用Z。数値と現役逆引きを結合、条件付き繁殖と持越しを直接付与から分離。公開提示の受領は別の有限段階。',f'新focused {tests}試験、task graph、決定性/check byte+mtime無変更 PASS。新native/ROM復元/旧受入再走0。最終indexのscope/private検査後だけcommit。')
    allowed=set(b.CODE)|{b.OUT+'/'+n for n in files}|{VERIFY,r.STATE,r.GUIDE,ENTRY}|LOGS
    guard=final_index(START,allowed,VERIFY);(WORK/'proof/index.json').write_bytes(r.encode(guard))
    (WORK/'proof/build.json').write_bytes(r.read(r.ROOT,VERIFY))
    commit=publish(b.TASK,source_head)
    snapshot({VERIFY,r.STATE,r.GUIDE,ENTRY,b.INDEX,*b.CODE,b.OUT+'/README.md',b.OUT+'/VEGA_BALANCE_INDEX.md',b.OUT+'/GMAX_INDEX.md',b.OUT+'/pokemon/24.md',b.OUT+'/moves/344.md',b.OUT+'/gmax/1441.md'})
    print(json.dumps({'status':'PUBLISHED_VERIFIED_RECEIPT_PENDING','commit':commit,'files':len(files),'links':links,'entry':b.OUT+'/README.md','semantic_sha256':index['semantic_sha256']}))


def receipt(source_head):
    observed=a.live(source_head);p=r.load(r.read(r.ROOT,PRESENTATION));index=r.load(r.read(r.ROOT,b.INDEX));proof=r.load(r.read(r.ROOT,VERIFY))
    r.need(p['entry_path']==b.OUT+'/README.md' and p['semantic_sha256']==index['semantic_sha256'] and p['tree_sha256']==index['tree_sha256'] and p['presented_to_owner'] is True and p['owner_approval_granted'] is False,'提示identity/承認区分不一致')
    r.need(bool(__import__('re').fullmatch('[0-9a-f]{40}',p['wiki_commit'])),'公開commit不正')
    run('git','merge-base','--is-ancestor',p['wiki_commit'],'HEAD')
    r.need(not a.git('diff','--name-only',p['wiki_commit'],'--',b.OUT).strip(),'提示した固定R0から変更あり')
    r.need(p['build_run_id']==proof['actions_run_id'] and proof['source_head']==index['source_head'] and proof['status']=='PASS','生成proof不一致')
    accepted=accepted_run(p['build_run_id'],index['source_head'],['R0の新しいfocused試験とtask graph','R0生成または提示receiptを検証して非force反映'])
    # 生成器を再走しない。公開済みR0の集合とhashだけ照合する。
    folder=r.ROOT/b.OUT;expected=set(index['files'])|{'data/index.json'}
    r.need({x.relative_to(folder).as_posix() for x in folder.rglob('*') if x.is_file()}==expected,'固定R0集合変更')
    for name,binding in index['files'].items():r.need(r.identity(r.read(r.ROOT,b.OUT+'/'+name))==binding,'固定R0 byte変更')
    value={'schema_version':1,'task':RECEIPT_TASK,'presentation':p,'completed_build_actions':accepted,'source_head':source_head,'status':'PASS_PUBLISHED_PRESENTED_R0','fixed_tree_files':len(expected),'accepted_generation_reruns':0,'accepted_test_reruns':0,'new_native_processes':0,'rom_reconstructions':0,'actions_run_id':int(os.environ['GITHUB_RUN_ID'])}
    write(RECEIPT,r.encode(value))
    state=r.load(r.read(r.ROOT,r.STATE));wiki=state['owner_execution_plan']['wiki'];r.need(not wiki['review_ready'],'提示受領済み。重複しない')
    wiki.update(status='READY_FOR_REVIEW',review_ready=True,presented_to_owner=True,published_commit=p['wiki_commit'],presentation_receipt_path=RECEIPT)
    wiki['completion_gates']['published_and_presented']=True
    state['owner_execution_plan']['phase']='SAVE_CAPACITY_INTEGRATION'
    state['owner_execution_plan']['owner_review']['status']='REFERENCE_PRESENTED_NO_APPROVAL'
    state['owner_execution_plan']['technical_lanes']['save_capacity']['status']='READY_TO_RESUME_FROM_PRESERVED_FRONTIER'
    saved=state['owner_execution_plan']['deferred_technical_resume']
    paths=saved['previous_next_action']['read_paths']
    value['technical_resume_bindings']={name:r.identity(r.read(r.ROOT,name)) for name in paths}
    write(RECEIPT,r.encode(value))
    state['next_action']={'id':'SAVE_CAPACITY_FROM_PRESERVED_08397492_FRONTIER','goal_ja':'固定R0提示済み。Weather Bubbleの保存原本784分類/90未知/安全容量0から、次の0x08397492と必要な保存controller容量/owner移管の未完を有限範囲で進める。','read_paths':['docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md',r.GUIDE,*paths],'done_ja':'対象の根拠を原本へ束縛し、必要容量と保存統合の残件を更新。最後の1件/安全容量獲得/全story PASSと誤記せず、無変更の成功原本は再走しない。'}
    state['observed_head_checks']=observed
    state['recording']['last_execution']={'task':RECEIPT_TASK,'source_head':source_head,'actions_run_id':int(os.environ['GITHUB_RUN_ID']),'completed_build_actions':accepted,'accepted_tests_rerun':0,'accepted_generation_reruns':0,'task_graph_passed':True,'new_native_processes':0,'rom_reconstructions':0}
    state['recording']['status']='R0_PUBLISHED_PRESENTED_SAVE_CAPACITY_NEXT'
    write(r.STATE,r.encode(state));write(r.GUIDE,guide(index,True))
    append_logs(RECEIPT_TASK,'実在する固定R0入口の会話提示、公開commit、意味/tree hash、完了した生成Actions全必須stepを結合。review_ready=true。承認0を保ち、次は保存容量lane。',f'公開tree {len(expected)}ファイルの集合/hash不変、生成run {p["build_run_id"]} completed/success、task graph PASS。生成/受入試験の再走0。最終metadata差分のprivate/scope検査後にcommit。')
    allowed={PRESENTATION,RECEIPT,r.STATE,r.GUIDE}|LOGS
    guard=final_index(p['wiki_commit'],allowed,RECEIPT);(WORK/'proof/index.json').write_bytes(r.encode(guard));(WORK/'proof/receipt.json').write_bytes(r.read(r.ROOT,RECEIPT))
    commit=publish(RECEIPT_TASK,source_head);snapshot({PRESENTATION,RECEIPT,r.STATE,r.GUIDE,b.INDEX})
    print(json.dumps({'status':'READY_FOR_REVIEW','commit':commit,'wiki_commit':p['wiki_commit'],'next':state['next_action']['id']}))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--tests',type=int,default=0);args=parser.parse_args()
    (WORK/'proof').mkdir(parents=True,exist_ok=True)
    if (r.ROOT/PRESENTATION).exists():receipt(os.environ['GITHUB_SHA'])
    else:build(os.environ['GITHUB_SHA'],args.tests)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        (WORK/'proof').mkdir(parents=True,exist_ok=True)
        (WORK/'proof/failure.json').write_bytes(r.encode({'status':'FAIL','error':str(exc).replace(str(r.ROOT),'$REPO'),'completion_not_claimed':True}))
        snapshot({VERIFY,RECEIPT,PRESENTATION,r.STATE,r.GUIDE,b.INDEX,*b.CODE})
        raise
