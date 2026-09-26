#!/usr/bin/env python3
"""固定の構築済みCircus候補で未受入の実勝敗とSave/Continueだけを実行。"""
from pathlib import Path
import json
import os
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_streak_probe as probe
from pr16_circus_identity import need,identity,strict,stable,replace_once
SELF='scripts/pr16_streak_native.py'
SOURCE='tools/mgba_pr16_streak_native.c'
TEST='tests/test_pr16_streak_native.py'
WORKFLOW='.github/workflows/pr16-streak-native.yml'
CHECKPOINT='content/modernization/pr16_circus_streak_build_checkpoint.json'
OUT=ROOT/'.local/pr16-streak-native'
INPUT=ROOT/'.local/pr16-streak-input'
WX='tools/mgba_pr16_bp_win_exchange.c'
BR='tools/mgba_pr16_bp_battle_return.c'
LEGACY='tools/mgba_pr16_circus_native.c'
EXTRA={WX,BR,LEGACY,'scripts/pr16_streak_probe.py',CHECKPOINT}

def function(text,name):
    matches=list(re.finditer(r'(?m)^static [^\n]+\b'+re.escape(name)+r'\([^;]*?\)\s*\{',text))
    need(len(matches)==1,'helper boundary: '+name)
    start=matches[0].start();at=matches[0].end();depth=1
    while at<len(text) and depth:
        depth+=(text[at]=='{')-(text[at]=='}');at+=1
    need(depth==0,'unclosed helper: '+name)
    return text[start:at]

def policy(wx,br):
    pieces=[function(wx,n) for n in ('wx_effect','wx_move_slot','wx_party_score','wx_cursor','wx_team','wx_reserve')]
    pieces[-1]=replace_once(pieces[-1],'if(i==active || !read16(c,mon+0x56U))continue;','if(!read16(c,mon+0x56U))continue;')
    pieces[-1]=replace_once(pieces[-1],'    unsigned best=6U;','    bp_require(c,active<3U,"active native index out of bounds");\n    unsigned best=6U;')
    match=re.search(r'struct BPReturn \{[^}]+\};',br);need(match is not None,'return witness struct absent');pieces.append(match[0])
    pieces.extend(function(br,n) for n in ('br_trace','br_move_menu','br_move'))
    body=pieces[-1];start=body.index('    for(unsigned i=0;i<4U;++i){');end=body.index('    br_trace(c,"turn-start");',start)
    need(body[start:end].count('if(m && p)')==1,'move selection source differs')
    pieces[-1]=body[:start]+'''    slot=wx_move_slot(c);
    move=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*slot);
    pp=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+slot);
'''+body[end:]
    return '\n\n'.join(pieces)+'\n'

def verify_recipe(recipe):
    saved=strict((ROOT/CHECKPOINT).read_bytes())
    need(saved['classification']=='CIRCUS_ISOLATED_STREAK_BUILT_NATIVE_OPEN' and recipe==saved['build'],'fixed build recipe differs')
    need(recipe['candidate']==dict(size=33554432,sha256=probe.SHA),'fixed candidate differs')
    for name,bound in recipe['source_bindings'].items():need(identity((ROOT/name).read_bytes())==bound,'build source changed: '+name)
    need(identity((INPUT/'candidate.gba').read_bytes())==recipe['candidate'],'native ROM differs')

def reconstruct():
    import pr16_circus_retention as parent
    from pr16_circus_streak import bounded_patch
    recipe=strict((ROOT/CHECKPOINT).read_bytes())['build'];raw=(parent.OUT/'candidate.gba').read_bytes()
    need(identity(raw)==recipe['parent'],'accepted parent differs')
    new=bounded_patch(raw,recipe['patches']);need(identity(new)==recipe['candidate'],'fixed successor differs')
    for row in recipe['allocation']['allocations']:
        need(identity(new[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'fixed allocation differs')
    INPUT.mkdir(parents=True,exist_ok=True)
    need(not any(p.is_symlink() for p in (INPUT,*INPUT.parents)),'unsafe native input')
    (INPUT/'candidate.gba').write_bytes(new);(INPUT/'report.json').write_bytes(stable(recipe));verify_recipe(recipe)
    return recipe

def adapt(text):
    from pr16_circus_retention_native import adapt_runner
    text=adapt_runner(text)
    text=replace_once(text,"scope='CIRCUS_RENTAL_RETENTION_FIRST_BATTLE_ONLY'","scope='CIRCUS_DEDICATED_STREAK_BATCH_SAVE_NATIVE'")
    text=replace_once(text,"recipe['entries']['bridge']","recipe['reception']['bridge']")
    text=replace_once(text,"recipe['entries']['circus']","recipe['reception']['circus']")
    text=replace_once(text,"        cfg=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_bytes())","        paths.update(EXTRA)\n        cfg=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_bytes())")
    text=replace_once(text,"            generated['controller.c']=(ROOT/SOURCE).read_text()","            generated['pr16_streak_legacy.c']=m.embed((ROOT/LEGACY).read_text(),'streak_unused_legacy')\n            generated['pr16_streak_policy.c']=policy((ROOT/WX).read_text(),(ROOT/BR).read_text())\n            generated['controller.c']=(ROOT/SOURCE).read_text()")
    return text

def run():
    import pr16_circus_native as native
    import pr16_circus_entry as parent
    reconstruct()
    first=strict((ROOT/'content/modernization/pr16_circus_first_battle_checkpoint.json').read_bytes())
    state=strict((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes())
    for name in (native.SELF,LEGACY):need(identity((ROOT/name).read_bytes())==first['original_sources'][name],'accepted helper changed: '+name)
    for name in (WX,BR):need(identity((ROOT/name).read_bytes())==state['source_bindings'][name],'historical policy helper changed: '+name)
    code=adapt((ROOT/native.SELF).read_text());ns=dict(native.__dict__);exec(compile(code,native.SELF,'exec'),ns)
    ns.update(SELF=SELF,SOURCE=SOURCE,TEST=TEST,WORKFLOW=WORKFLOW,OUT=OUT,SHA=probe.SHA,
        requested_cases=lambda:(probe.CASE,),validate=probe.validate,verify_recipe=verify_recipe,
        EXTRA=EXTRA,LEGACY=LEGACY,WX=WX,BR=BR,policy=policy)
    old=parent.OUT
    try:parent.OUT=INPUT;result=ns['run']()
    finally:parent.OUT=old
    if result['status']=='PASS_CIRCUS_SCOPED_NATIVE':
        events=probe.parse((OUT/(probe.CASE+'.stderr')).read_bytes())
        summary=probe.analyze(events,result['results'][0]['result'])
        summary.update(tested_head=result['source_head'],run_id=int(os.environ.get('GITHUB_RUN_ID','0')),
            candidate=result['candidate'],native_processes=1,fresh_cores=2,accepted_native_cases_replayed=0,
            raw_stdout=identity((OUT/(probe.CASE+'.stdout')).read_bytes()),raw_stderr=identity((OUT/(probe.CASE+'.stderr')).read_bytes()))
        (OUT/'events.json').write_bytes(stable(events));(OUT/'streak.json').write_bytes(stable(summary))
    print(json.dumps({k:result[k] for k in ('status','actual_new_processes','successful_fresh_cores','failures')},ensure_ascii=False))
    return result
if __name__=='__main__':sys.exit(0 if run()['status']=='PASS_CIRCUS_SCOPED_NATIVE' else 1)
