#!/usr/bin/env python3
"""保存原本で証明された今回3caseのHP不整合だけを失効し、正規HPで再検証。"""
from __future__ import annotations
import copy
import json
import re
import struct
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_exp_multilevel as g
x=g.x
SELF='scripts/pr16_exp_health_policy.py'
TEST='tests/test_pr16_exp_health_policy.py'
x.CODE.update((SELF,TEST))
LEGACY_RUN=36065509607
HEALTH_RUN=36067198527
IMPACTED={'butterfree-exp-known','butterfree-exp-replace','butterfree-exp-summary-refuse'}
original_pending=x.pending
original_run=g.original_run
original_publish=x.publish
retired={}


def health(stderr,before,delta):
    rows=re.findall(rb'^NATURAL_PARTY stage=(fixture|returned|saved|continued) counter=(\d+) hex=([0-9a-f]{200})$',stderr,re.M)
    x.need([r[0] for r in rows]==[b'fixture',b'returned',b'saved',b'continued'] and [int(r[1]) for r in rows]==[2,2,3,3],'exact health lifecycle')
    phases={}
    for label,_,encoded in rows:
        data=bytes.fromhex(encoded.decode());hp,maximum=struct.unpack_from('<HH',data,86)
        phases[label.decode()]={'hp':hp,'maximum_hp':maximum,'level':data[84]}
    first=phases['fixture'];last=phases['returned']
    x.need(type(before)is int and type(delta)is int and first['level']==before and before+delta<=last['level']<100,'health levels')
    x.need(last==phases['saved']==phases['continued'],'health persistence')
    valid=first['hp']==first['maximum_hp'] and all(0<p['hp']<=p['maximum_hp']<999 for p in phases.values())
    return {'status':'PASS' if valid else 'INVALID_HP_FIXTURE','phases':phases,'source':x.identity(stderr)}


def review(accepted,reader):
    retired_now={};retained={}
    for name,a in accepted.items():
        fixture=a['result']['fixture'];h=health(reader(name,a),fixture['level'],fixture['min_delta'])
        if h['status']=='PASS':retained[name]=h;continue
        p=h['phases'];legacy={'hp':999,'maximum_hp':106,'level':44}
        x.need(name in IMPACTED and a['run_id']==LEGACY_RUN and p['fixture']=={'hp':999,'maximum_hp':999,'level':43} and all(p[s]==legacy for s in ('returned','saved','continued')),'unreviewed health impact; do not replay')
        retired_now[name]={'prior_acceptance':copy.deepcopy(a),'observed_health':h,'reason_ja':'今回保存3caseの帰還/Save/ContinueがHP999>最大HP106。HP保存整合性gate追加の変更影響が原本で確定。旧moves/PP証拠は不変の履歴として保持。'}
    return retired_now,retained


def evidence(name,a):
    folder=x.ROOT/x.EVIDENCE/str(a['run_id']);v=x.load(folder/'verification.json');p=folder/(name+'.stderr.txt')
    raw=p.read_bytes();x.need(x.identity(raw)==v['proof_bindings'][p.name],'immutable saved stderr')
    return raw


def reviewed_pending(cases,accepted):
    """Mutate only this attempt's in-memory acceptance map, before any native run."""
    removed,retained=review(accepted,evidence);retired.update(removed)
    for name in removed:del accepted[name]
    x.write(x.PROOF/'health-impact.json',{'retired':removed,'retained':retained,'accepted_case_rerun_reason':'observed HP > max HP in immutable previous Save/Continue','candidate_changes':0})
    return original_pending(cases,accepted)


def verify_unit(run,count):
    folder=x.ROOT/x.EVIDENCE/str(run);v=x.load(folder/'verification.json')
    x.need(v['new_unit_tests']==count,'saved unit count')
    for leaf in ('unit.stdout.txt','unit.stderr.txt','unit.process.json'):
        x.need(x.identity((folder/leaf).read_bytes())==v['proof_bindings'][leaf],'unit raw proof')
    x.need(x.load(folder/'unit.process.json')=={'returncode':0,'timed_out':False},'unit success')
    return v


def scoped_run(command,name,*args,**kwargs):
    if name=='unit':
        original=verify_unit(LEGACY_RUN,20);recent=verify_unit(HEALTH_RUN,9)
        for path,digest in g.UNIT_SOURCES.items():
            x.need(x.identity((x.ROOT/path).read_bytes())['sha256']==digest==original['source_bindings'][path]['sha256'],'base oracle changed')
        x.need(x.identity((x.ROOT/g.SELF).read_bytes())==recent['source_bindings'][g.SELF],'old health oracle changed')
        current=(x.ROOT/g.TEST).read_text();old=current.replace("'offset=90;offset<=98'","'offset=v->min_delta>1?90:86'")
        x.need(current!=old and x.identity(old.encode())==recent['source_bindings'][g.TEST],'only old structure assertion may change')
        command=[sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_boundaries.BoundaryTests.test_observation_never_calls_accepted_main','tests.test_pr16_exp_multilevel.HealthTests.test_native_fixture_writes_only_combat_stats','tests.test_pr16_exp_health_policy','-v']
        x.write(x.PROOF/'unit-reuse.json',{'unchanged_base_oracles':19,'unchanged_health_oracles':7,'source_runs':[LEGACY_RUN,HEALTH_RUN],'changed_structure_checks':2,'new_impact_tests':8})
    out,err=original_run(command,name,*args,**kwargs)
    if name in {c[0] for c in x.CASES}:
        r=json.loads(out);h=health(err,r['level_before'],2 if name=='butterfree-exp-multilevel' else 1)
        x.need(h['status']=='PASS','new native Save/Continue health gate');x.write(x.PROOF/(name+'.health.json'),h)
    return out,err


def publish(v):
    from pr16_learnset_compact_record import publish_resume
    logs={name:(x.ROOT/name).stat().st_size for name in ('design/run_log.md','design/version_log.md')}
    original_publish(v)
    guide=x.ROOT/x.GUIDE;text=guide.read_text()
    old='ARM/原本生成/ROM変更/受入済みcase再実行は0。'
    x.need(text.count(old)==1,'exact guide scope correction')
    text=text.replace(old,'ARM/原本生成/ROM変更と、変更影響がない受入済みcase再実行は0。')
    text+='\n## HP保存整合性の変更影響\n\n初回run36065509607の3caseは技/PP検査成功だが、保存原本でHP999>最大HP106を確認したため、現行HP gateの受入から失効。履歴は上書きせずsuperseded_acceptancesとhealth-impact.jsonへ保存。複数レベル上昇の正常HP成功run36067198527は再実行しない。今回の変更影響あり再実行は '+str(v.get('change_impact_native_reruns',0))+' case、影響なしの受入済み再実行は0。\n\n'
    for name,h in v.get('native_health',{}).items():
        p=h['phases'];text+=f"- `{name}`: Lv{p['fixture']['level']} HP {p['fixture']['hp']}/{p['fixture']['maximum_hp']} → Lv{p['returned']['level']} HP {p['returned']['hp']}/{p['returned']['maximum_hp']}。通常Save/fresh Continue一致。run `{h['run_id']}`。\n"
    text+='\n新HP gateでも開始個体/EXP/能力/進行はfixture。野生/配布/孵化/form/進化/共有EXP全体の受入へ昇格しない。今回の選択経路は `scripts/pr16_exp_health_policy.py`。追加unitは累計36種、最新実行'+str(v['new_unit_tests'])+'件。変更なし26件はhash付き成功原本で照合する。\n'
    guide.write_text(text)
    state=x.load(x.ROOT/x.m.STATE);section=state['learnset_exp_boundaries']
    section.update(health_policy=v.get('health_policy'),native_health=v.get('native_health',{}),superseded_case_names=sorted(v.get('superseded_acceptances',{})),change_impact_native_reruns=v.get('change_impact_native_reruns',0),unaffected_accepted_native_reruns=0)
    state['source_bindings'][x.GUIDE]=x.identity(guide.read_bytes())
    state['next_action']['read_paths']=[x.GUIDE,x.CP,SELF,TEST]
    publish_resume(state)
    for name,start in logs.items():
        path=x.ROOT/name;raw=path.read_bytes();tail=raw[start:].decode()
        tail=tail.replace('旧受入再実行0','変更影響なしの旧受入再実行0')
        tail+=f"- Health impact: 原本HP999/最大HP106の今回3caseを現行gateから失効。変更影響ありnative再実行{v.get('change_impact_native_reruns',0)}、影響なし0。正常multi-level成功は継承。HP/max HPは生成値のまま、観測中の書込禁止と警告拒否を維持。\n"
        tail+=f"- Focused scope: 追加unit累計36種。最新{v['new_unit_tests']}件（対象は新影響8+変更構造2）、保存26件の原本を照合。原本ROM生成/ARM build/候補変更0。\n"
        tail+='- Upstream read-only reference: https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/learn_move.c の既存ABIを補助確認。lock更新なし。HP修復の根拠は今回の保存原本。\n'
        path.write_bytes(raw[:start]+tail.encode())


def execute():
    retired.update(x.load(x.ROOT/x.CP).get('superseded_acceptances',{}))
    try:x.execute()
    finally:
        p=x.PROOF/'verification.json'
        if p.exists():
            v=x.load(p)
            def reader(name,a):
                return (x.PROOF/(name+'.stderr.txt')).read_bytes() if a['run_id']==v['run_id'] else evidence(name,a)
            removed,healthy=review(v['accepted'],reader);retired.update(removed)
            for name in removed:del v['accepted'][name]
            if removed:v['status']='PARTIAL_BATTLE_EXP_BOUNDARIES'
            v['superseded_acceptances']=retired
            v['health_policy']='All four current EXP cases require native initial HP/max HP and consistent Save/Continue HP.'
            v['change_impact_native_reruns']=sum((x.PROOF/(name+'.process.json')).exists() for name in retired)
            v['accepted_case_reruns']=v['change_impact_native_reruns'];v['unaffected_accepted_native_reruns']=0
            v['native_health']={name:dict(h,run_id=v['accepted'][name]['run_id']) for name,h in healthy.items()}
            x.write(p,v)


if __name__=='__main__':
    x.pending=reviewed_pending;x.m.run=scoped_run;x.publish=publish
    actions={'execute':execute,'record':x.record,'complete':x.complete,'guard':x.guard,'paths':lambda:print('\n'.join(sorted(x.owned())))}
    x.need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths');actions[sys.argv[1]]()
