#!/usr/bin/env python3
"""明示的非学習ownerを自動補完せず、17学習ownerの配布を独立受入。"""
import datetime
import json
import os
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo
import pr16_collection_gifts as c
need=c.need
SELF='scripts/pr16_collection_gift_scope.py'
TEST='tests/test_pr16_collection_gift_scope.py'
STATUS='PASS_COLLECTION_GIFTS_LEARNING_SCOPE'
EXCLUDED=1281
POLICY='EXCLUDED_REMAKE_FORM_IDENTITY_ONLY'
NEXT=('Issue19: Collection学習owner17経路の通常配布・原本初期技・Save/fresh Continueは保存受入から再実行しない。'
      'ギザみみピチュー1281は既存EXCLUDED_REMAKE_FORM_IDENTITY_ONLYにより技の自動補完/通常ピチュー流用禁止、'
      '配布初期技の受入保留。未受入の研究タマゴ孵化後のform/技保持、釣り/隠し野生の特殊技順を続ける。'
      '全Issue19/release/active baseline切替は未完。')


def split_cases(model, rows, pp, index):
    need(len(model['gifts'])==18,'全18配布定義')
    fixed=[g for g in model['gifts'] if g['kind']=='FIXED']
    need(len(fixed)==3 and sorted(g['claim_bit'] for g in fixed)==[0,1,2],'固定3claim')
    level={}
    for row in index:
        if row['consumer']=='level_up':
            need(row['species_id'] not in level,'重複source owner');level[row['species_id']]=row
    excluded=[];cases=[];seen=set()
    for i,g in enumerate(model['gifts']):
        fi=g['form_index'];need(type(fi)is int and 0<=fi<len(model['forms']),'form index')
        form=model['forms'][fi];sid=form['target_species'];kind=g['kind']
        need(type(sid)is int and 0<sid<1671 and sid not in seen,'明示owner/重複');seen.add(sid)
        need(kind in ('FIXED','RESEARCH_EGG'),'配布kind')
        egg=int(kind=='RESEARCH_EGG');need(g['kind_id']==egg and form['method']==('RESEARCH_EGG' if egg else 'FIXED_GIFT'),'配布/フォームkind一致')
        need(type(g['unlock_id'])is int and 0<=g['unlock_id']<=18,'unlock境界')
        need(sid in level,'source owner欠落');source=level[sid]
        if sid==EXCLUDED:
            identity=source.get('identity',{})
            need(source['species_key']=='SPECIES_KEY_PICHU_SPIKY' and source['status']=='IDENTITY_ONLY_NO_REPLACEMENT'
                 and source['payload'] is None and identity==dict(automatic_fallback=False,policy=POLICY,preserve_current_moves=True,
                     preserve_identity=True,species_id=EXCLUDED,species_key='SPECIES_KEY_PICHU_SPIKY'),'既存除外方針そのまま')
            need(not egg and sid not in rows,'非学習ownerへの技表注入禁止')
            excluded.append(dict(gift_index=i,form_index=fi,species=sid,policy=POLICY,source=source,
                status='NOT_ACCEPTED_IDENTITY_ONLY_NO_AUTOFILL',reason_ja='原本学習ownerではない。通常ピチューの技や空4技を期待値にしない。'))
            continue
        need(source['status']=='PAYLOAD_PREPARED_NOT_INSTALLED' or sid==1029 and source['status']=='BLOCKED_SOURCE_ADOPTION','既採用原本owner')
        need(sid in rows and rows[sid],'原本技の欠落 '+str(sid))
        level_value=1 if egg else 50;moves=c.s.boundary.n.initial(rows[sid],level_value)
        need(any(moves),'非空原本初期技');p=[pp[x] if x else 0 for x in moves]
        need(all(type(x)is int and 1<=x<=64 for x,m in zip(p,moves) if m),'PP原本')
        cases.append(dict(name=('research-egg-' if egg else 'fixed-form-')+str(sid),gift_index=i,form_index=fi,species=sid,
            level=level_value,is_egg=egg,claim_bit=g['claim_bit'],display_name=g['display_name'],moves=moves,pp=p,
            original_rows=[list(x) for x in rows[sid]],unlock_id=g['unlock_id']))
    need(len(excluded)==1 and len(cases)==17 and sum(x['is_egg'] for x in cases)==15,'17学習owner+明示除外1')
    return sorted(cases,key=lambda v:(v['is_egg'],v['gift_index'])),excluded


def scoped_vectors(model,rows,pp):
    # 旧22unitはsource不変の保存原本を継承。この9試験のみ追加。
    _,err=c.m.run([sys.executable,'-B','-m','unittest','tests.test_pr16_collection_gift_scope','-v'],'scope-unit')
    count=re.search(rb'Ran (\d+) tests? in ',err);need(count and b'\nOK\n' in err,'policy unit result')
    index=[json.loads(x,object_pairs_hook=c.egg.strict_pairs) for x in (c.WORK/'payload/consumer-index.jsonl').read_bytes().splitlines()]
    cases,excluded=split_cases(model,rows,pp,index)
    c.write(c.PROOF/'scope.json',dict(schema_version=1,new_scope_unit_tests=int(count[1]),
        candidate=c.CANDIDATE,learning_cases=17,defined_routes=18,excluded=excluded,
        old_unit_reruns=0,policy_changes=0,automatic_fallback=False,all_owners_accepted=False))
    return cases


def execute():
    c.vectors=scoped_vectors;c.CODE|={SELF,TEST}
    try:c.execute()
    finally:
        path=c.PROOF/'verification.json'
        if path.exists():
            v=c.load(path)
            if (c.PROOF/'scope.json').exists():
                v['scope']=c.load(c.PROOF/'scope.json');v['new_scope_unit_tests']=v['scope']['new_scope_unit_tests']
                if len(v['accepted'])==17 and not v['failures'] and v['status']=='PARTIAL_COLLECTION_GIFTS':v['status']=STATUS
            v['proof_bindings']={p.name:c.identity(p.read_bytes()) for p in c.PROOF.iterdir() if p.is_file() and p.name!='verification.json'}
            c.write(path,v)


def publish(v,completion=False):
    from pr16_learnset_compact_record import publish_resume
    good=list(v['accepted']);pending=[n for n in v.get('contracts',{}) if n not in good]
    confirmed=v['actions_completion_confirmed'];date=datetime.datetime.now(datetime.timezone.utc)
    nextstep=NEXT if confirmed else ('17学習ownerの保存成功native/旧unit/host/ARMを再実行せず、Actions/artifact終端照合だけ実施。' if len(good)==17 and not v['failures'] else 'Collection配布の失敗原本を確認し未成功caseだけ修復。受入済みcaseは再実行しない。')
    text=f'# PR16 Issue19: Collection学習owner配布\n\n状態 `{v["status"]}`。学習owner限定受入 {len(good)}/17、定義全体18件中1件は既存方針で保留。Actions終端 `{confirmed}`。\n\nsource `{v["source_head"]}` / run `{v["run_id"]}`。候補 `{c.CANDIDATE["sha256"]}` / 33554432 bytes。ROM/runtime/原本方針は変更しない。\n\n## 範囲と保留\n\n固定form2と研究タマゴ15。初期party、開始場所、全unlock、未受領ownerはfixture。実NPCのroot/menu/page/選択、配布、原本初期技/PP、通常Save、fresh-core Continue、再訪取消を検証。ストーリー到達・研究ランク獲得・研究タマゴ孵化は含まない。7host書込APIを拒否し、getterはguard区間間の読み取り補助として分離。\n\nギザみみピチュー1281は `EXCLUDED_REMAKE_FORM_IDENTITY_ONLY` / `IDENTITY_ONLY_NO_REPLACEMENT` / payloadなし。自動fallback禁止・既存4技保持を優先し、通常ピチューの技流用や空4技を成功期待値にしていない。この配布初期技は未受入。初回run36110983368はこの期待値境界で停止、native/host0。旧22unit成功原本を継承し再実行しない。\n\n| case | species | level | egg | 原本4技 | 実測run |\n| --- | ---: | ---: | ---: | --- | ---: |\n'
    for name,a in v['accepted'].items():
        r=a['result'];text+=f'| {name} | {r["species"]} | {r["level"]} | {r["is_egg"]} | {r["moves"]} | {a["run_id"]} |\n'
    text+=f'\n未成功学習owner `{pending}`。全party200byte/元party100byte、owner CRC/claim bit、4技/PP/PP Ups/HP/egg getter、frame/counterをraw textで照合。固定claim保持は確認するが、二重受取の実選択は含まない。\n\n今回新scope-unit {v.get("new_scope_unit_tests",0)}、旧unit実行 {v["new_unit_tests"]}、host compile {v["host_compiles"]}、native {v["native_processes"]}。受入済み自然配布/孵化3・EXP/Bag/egg8/旧野生/ARM/Wikiは再実行しない。\n\n## 次\n\n{nextstep}\n'
    (c.ROOT/c.GUIDE).write_text(text)
    state=c.load(c.ROOT/c.m.STATE)
    state['learnset_collection_gifts']={k:v[k] for k in ('status','source_head','run_id','candidate','actions_completion_confirmed','issue19_complete')}
    state['learnset_collection_gifts'].update(path=c.CP,accepted_cases=good,pending_cases=pending,excluded_identity_only=[1281],defined_routes=18,learning_routes=17)
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_date_jst']=date.astimezone(ZoneInfo('Asia/Tokyo')).date().isoformat()
    state['observed_head_semantics']='Collection学習owner17経路と非学習owner1281を区別。全18配布/全Issue19完成ではない。'
    state['observed_head_checks']=dict(scope_head=v['source_head'],runs=v.get('terminal_actions',[dict(id=v['run_id'],status='in_progress',conclusion=None)]),reason_ja='実測とActions終端を区別。一般CI/全体完成へ昇格しない。')
    state['bp']['current_stop']=f'Issue19: Collection学習owner {len(good)}/17。非学習owner1281の配布初期技は未受入。';state['bp']['next_step']=nextstep
    state['next_action']=dict(state['next_action'],id='COLLECTION_GIFTS' if not confirmed else 'SPECIAL_WILD_AND_RESEARCH_HATCH',goal_ja=nextstep,read_paths=[c.GUIDE,c.CP,SELF,c.SELF])
    for p in c.CODE|{SELF,TEST,c.CP,c.GUIDE}:state['source_bindings'][p]=c.identity((c.ROOT/p).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    note=f'\n## {date.isoformat()}\n- Timestamp: {date.isoformat()}\n- Task: {c.TASK}\n- Version: issue19-collection-learning-owner-v1\n- Status: '+('DONE（学習owner17限定、1281/全体は未完）' if confirmed else 'STOPPED（原本保存から未完だけ継続）')+f'\n- Summary: 実NPC配布/原本初期技/Save/fresh Continue {len(good)}/17。初期party/場所/unlock/claimはfixture。1281は非学習owner方針により自動補完禁止・未受入。研究タマゴ孵化未受入。\n- Files changed: 明示scope/9新unit/限定Actions、checkpoint/guide/原本text、固定引継ぎMD/JSON、両ログ。\n- Verify: 新scope-unit{v.get("new_scope_unit_tests",0)}、旧unit実行{v["new_unit_tests"]}、host{v["host_compiles"]}、native{v["native_processes"]}。Actions終端{confirmed}、終端専用={completion}（専用時native/旧unit/host/ARM0）。\n- Commit: 同branch非force push・reflected-head/remote照合。\n- Network: 固定GitHub原本/保存artifact/Actionsのみ。ROM/seed非追跡。受入済み3/EXP/Bag/egg8/旧野生/ARM/Wiki不変。merge/release/baseline切替なし。\n'
    for p in ('design/run_log.md','design/version_log.md'):
        with (c.ROOT/p).open('a') as f:f.write(note)


def record():
    c.publish=publish;c.CODE|={SELF,TEST};c.record()


if __name__=='__main__':
    actions=dict(execute=execute,record=record,guard=c.guard,paths=lambda:print('\n'.join(sorted(c.owned()))))
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|guard|paths');actions[sys.argv[1]]()
