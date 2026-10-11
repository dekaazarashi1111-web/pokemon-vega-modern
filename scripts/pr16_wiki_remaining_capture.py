#!/usr/bin/env python3
"""Issue18残件用の限定source inventory。既存原文・候補を読むだけ。"""
from __future__ import annotations
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import Inputs, ROOT, STATE, digest, need, selected_candidate, stable
from pr16_candidate_wiki_consumers import load

OUTPUT = 'content/modernization/pr16_wiki_remaining_source_inventory.json'
RECEIPT = 'content/modernization/pr16_candidate_wiki_acceptance.json'
PATTERN = re.compile(r'gMovesThatChangePhysicality|CalcMoveSplit|GiveMonInitialMoveset|FLAG_WILD_CUSTOM_MOVES|FLAG_HIDDEN_ABILITY|DetermineEggAbility|ABILITY_PATCH|AbilityPatch|hiddenAbility|move_effects')


def contexts(text: str, radius: int = 4) -> list[dict]:
    lines = text.splitlines(); intervals = []
    for index, line in enumerate(lines):
        if PATTERN.search(line):
            lo, hi = max(0, index-radius), min(len(lines), index+radius+1)
            if intervals and lo <= intervals[-1][1]:
                intervals[-1][1] = max(hi, intervals[-1][1])
            else:
                intervals.append([lo, hi])
    return [{'start_line': lo+1, 'end_line': hi, 'text': '\n'.join(lines[lo:hi])+'\n'} for lo, hi in intervals]


def remote_json(url: str) -> dict:
    headers = {'Accept': 'application/vnd.github+json'}
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer '+token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=45) as response:
        raw = response.read(3_000_001)
    need(len(raw) <= 3_000_000, 'API応答size超過')
    return json.loads(raw)


def collect() -> dict:
    inp = Inputs(); candidate = selected_candidate(inp); source = load(inp)
    names = ('CalcMoveSplit', 'CreateWildMon', 'ScriptGiveMon', 'DetermineEggAbility',
             'GetTypeBasedZMove', 'CanUseZMove')
    units = {name: {'text': source.code(name), 'proof': source.proof(name)} for name in names}
    source_model = inp.json('content/modernization/pr16_candidate_wiki_source_model.json')
    # scope限定source探索。文書・ROM・private領域は検索しない。
    paths = subprocess.check_output(['git','ls-files','--','scripts/*.py','overlays/**/*.c','overlays/**/*.h'],cwd=ROOT).decode().splitlines()
    local = {}
    for name in paths:
        if 'wiki' in name or '/pr16_' in name or '/test' in name:
            continue
        raw = inp.path(name).read_bytes()
        if len(raw) > 3_000_000:
            continue
        snippets = contexts(raw.decode('utf-8'))
        if snippets:
            local[name] = {'size':len(raw),'sha256':digest(raw),'contexts':snippets}
    commit = source.value['source_commit']
    path = 'assembly/data/move_tables.s'
    url = f'https://api.github.com/repos/kapibarasan000/CFRU-JP/contents/{path}?ref={commit}'
    info = remote_json(url)
    import base64, hashlib
    raw = base64.b64decode(info['content'])
    need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == info['sha'], '上流blob SHA不一致')
    text = raw.decode(); match = re.search(r'^gMovesThatChangePhysicality:\s*\n(.*?)(?=^\w+:|\Z)',text,re.M|re.S)
    need(match is not None, 'physicality tableがない')
    table = match[0].split('\n\n',1)[0]+'\n'
    model = {'schema_version':1,'candidate':candidate,'source_head':os.environ['GITHUB_SHA'],
             'source_commit':commit,'source_repository':'kapibarasan000/CFRU-JP',
             'units':units,'physicality_table':{'path':path,'commit':commit,'blob_sha':info['sha'],
                 'file_sha256':digest(raw),'start_line':text[:match.start()].count('\n')+1,'text':table},
             'move_categories':source_model['move_categories'],
             'local_sources':local,'new_native_runs':0,'arm_builds':0,'rom_changes':0,
             'scope':'LOCKED_SOURCE_INVENTORY_NOT_RUNTIME_ACCEPTANCE'}
    need(len(stable(model)) < 600_000, '限定inventory size超過')
    return model


def record(model: dict) -> None:
    from pr16_resume import DOC, render
    inp = Inputs(); receipt = inp.json(RECEIPT)
    previous = remote_json('https://api.github.com/repos/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/35546455254')
    need(previous['status']=='completed' and previous['conclusion']=='success' and previous['head_sha']=='479f02fb059215e4f9f4da86895b85e8a373b5ee','前回Wiki run照合失敗')
    receipt['verification_run_reconciled'] = {k:previous[k] for k in ('id','head_sha','status','conclusion')}
    receipt['verification_run_status_at_recording'] = 'completed: success（GETでpush/upload完了を照合）'
    receipt['remaining_source_inventory'] = {'path':OUTPUT,'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'scope':model['scope']}
    (ROOT/OUTPUT).write_bytes(stable(model)); (ROOT/RECEIPT).write_bytes(stable(receipt))
    state = inp.json(STATE)
    state['candidate_wiki']['verification_run_status']='completed_success'
    state['candidate_wiki']['remaining_source_inventory']=receipt['remaining_source_inventory']
    state['bp']['current_stop']=f"前回Wiki run35546455254のpush/upload成功をGET照合。Issue18残件の固定source inventoryを{OUTPUT}へ保存。Wiki本体の残件は未完。"
    state['next_action']['goal_ja']='Issue18の固定source inventoryから残件監査を実装し、既存generatorへ接続。完了済みCLI/静的Z対応/nativeを再実装・再実行しない。'
    state['bp']['next_step']=state['next_action']['goal_ja']
    state['logs_synchronized']=True
    (ROOT/STATE).write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n');(ROOT/DOC).write_text(render(state))
    now=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    for name in ('design/run_log.md','design/version_log.md'):
        with (ROOT/name).open('a',encoding='utf-8') as out:
            out.write(f'\n\n## {now} — Issue18残件source checkpoint\n- Task: USER-20260921-P08-CANDIDATE-WIKI / 限定source inventory\n- Status: STOPPED（source固定完了、残件実装へ継続）\n- Summary: 前回Wiki run35546455254をsuccessとして照合。既存consumer原文を再利用し、固定上流physicality tableのGit blob SHAと候補選択を照合。\n- Files changed: 専用capture/試験/workflow、残件source inventory、受入JSON、固定引継ぎMD/JSON、両ログ。\n- Verify: capture試験、候補正本間identity、上流Git blob SHA、task graph、resume、diff、changed-final-index private guard。native0/ARM0/ROM変更0。\n- Commit: この記録を含むcommit。source HEAD={os.environ["GITHUB_SHA"]}\n- Network: GitHub API run35546455254、kapibarasan000/CFRU-JP@{model["source_commit"]}/assembly/data/move_tables.s。固定sourceのみ。\n- Boundary: Issue18全体・release未完。Stage61/active baseline変更0。現HEADの無関係CI action_requiredをWiki失敗と混同しない。\n')


def guard() -> None:
    import pr16_wiki_checkpoint as checkpoint
    checkpoint.ALLOWED.add(OUTPUT)
    checkpoint.guard()

if __name__=='__main__':
    if sys.argv[1:] == ['guard']:
        guard()
    else:
        value=collect();record(value)
        print(json.dumps({'status':'PASS_SOURCE_INVENTORY','local_sources':len(value['local_sources']),'move_categories':list(value['move_categories']),'new_native_runs':0},ensure_ascii=False))
