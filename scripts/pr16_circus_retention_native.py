#!/usr/bin/env python3
"""Circus保持修復候補の個体継承だけを検証する。旧診断/初戦ターンは再実行しない。"""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_identity as trace
import pr16_circus_retention as build
need,identity,stable,strict=trace.need,trace.identity,trace.stable,trace.strict
SELF='scripts/pr16_circus_retention_native.py'
OUT=ROOT/'.local/pr16-circus-retention-native'
CONTROLLER='.local/pr16-circus-retention-input.c'


def retained(raw,stderr,code,case,sha):
    saved=trace.SHA
    try:
        trace.SHA=sha;row=trace.validate(raw,stderr,code,case)
    finally:trace.SHA=saved
    a=trace.analyze(trace.parse_events(stderr))
    need(a['classification']=='CIRCUS_RENTAL_IDENTITY_RETAINED','selected individuals were still replaced')
    need(a['selected_to_second_all_300_bytes_equal'] is True and a['second_to_action_all_300_bytes_equal'] is True,'selected 300bytes changed')
    need(a['first_changed_event'] is None,'intermediate replacement occurred')
    return row


def verify_recipe(recipe):
    need(recipe['status']=='BUILT_CIRCUS_RETENTION_NATIVE_OPEN' and recipe['parent']==build.PARENT,'retention build scope')
    need(recipe['independent_new_runtime_links']==recipe['independent_bounded_builds']==2,'independent successor construction')
    need(recipe['accepted_native_cases_replayed']==recipe['new_emulator_processes']==0,'builder native accounting')
    for name,binding in recipe['sources'].items():need(identity((ROOT/name).read_bytes())==binding,'retention build source differs: '+name)
    raw=(ROOT/'.local/pr16-circus-entry/candidate.gba').read_bytes();new=(build.OUT/'candidate.gba').read_bytes()
    need(identity(raw)==build.PARENT and identity(new)==recipe['candidate'],'retention candidate identity')
    proof=recipe['proof'];need(proof['literal_offset']==build.LITERAL and proof['script_continuations']==list(build.CONTINUATIONS),'retention ABI differs')
    offset=proof['payload_offset'];payload=new[offset:offset+proof['payload']['size']]
    need(identity(payload)==proof['payload'],'retention payload differs')
    need(build.bounded_patch(raw,build.LITERAL,offset,payload,proof['previous_entry'],proof['new_entry'])==new,'retention rollback proof')
    need(proof['new_entry']==build.BASE+offset+1 and proof['whole_rom_rollback_matches_parent'] is True,'entry proof')
    need(recipe['entries']==recipe['parent_recipe']['entries'] and recipe['launch_sites']==recipe['parent_recipe']['launch_sites'],'entry paths changed')
    return True


def adapt_runner(text):
    start=text.index("        saved=strict((ROOT/'content/modernization/pr16_circus_thumb_checkpoint.json').read_bytes())")
    end=text.index("        need(identity((ROOT/previous.control.SOURCE).read_bytes())",start)
    old=text[start:end]
    need(old.count('validate_build(recipe,saved[\'proof\'])')==1 and old.count("saved['build']")==2,'accepted runner binding block changed')
    text=text[:start]+'        verify_recipe(recipe)\n'+text[end:]
    text=trace.replace_once(text,"scope='THUMB_REPAIRED_CIRCUS_FIRST_BATTLE_ONLY'","scope='CIRCUS_RENTAL_RETENTION_FIRST_BATTLE_ONLY'")
    return text


def run():
    import pr16_circus_native as native
    import pr16_circus_entry as parent
    recipe=strict((build.OUT/'report.json').read_bytes());verify_recipe(recipe);sha=recipe['candidate']['sha256']
    original=strict((ROOT/'content/modernization/pr16_circus_first_battle_checkpoint.json').read_bytes())
    source=(ROOT/native.SOURCE).read_text();runner=(ROOT/native.SELF).read_text()
    for name,data in ((native.SOURCE,source),(native.SELF,runner)):
        need(identity(data.encode())==original['original_sources'][name],'accepted helper changed: '+name)
    path=ROOT/CONTROLLER;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(trace.instrument(source))
    namespace=dict(native.__dict__);exec(compile(adapt_runner(runner),str(ROOT/native.SELF),'exec'),namespace)
    namespace.update(SELF=SELF,SOURCE=CONTROLLER,TEST=build.TEST,WORKFLOW=build.WORKFLOW,OUT=OUT,SHA=sha,
        requested_cases=lambda:(trace.CASE,),validate=lambda raw,err,code,case:retained(raw,err,code,case,sha),verify_recipe=verify_recipe)
    old_out=parent.OUT
    try:
        parent.OUT=build.OUT;result=namespace['run']()
    finally:parent.OUT=old_out
    need(result['status']=='PASS_CIRCUS_SCOPED_NATIVE' and result['actual_new_processes']==1 and len(result['guard_checks'])==7,'retention native failed: '+str(result['failures']))
    raw=(OUT/(trace.CASE+'.stderr')).read_bytes();events=trace.parse_events(raw);a=trace.analyze(events)
    a.update(classification='CIRCUS_SELECTED_300_BYTES_RETAINED_FIRST_BATTLE',candidate=result['candidate'],tested_head=result['source_head'],
        run_id=int(os.environ.get('GITHUB_RUN_ID','0')),native_processes=1,fresh_cores=1,host_write_barriers=7,
        raw_stderr=identity(raw),rental_identity_verified=True,physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        accepted_native_cases_replayed=0,original_identity_diagnostic_run_reused=35378203102,proof=recipe['proof'])
    (OUT/'retention.json').write_bytes(stable(a));(OUT/'events.json').write_bytes(stable(events))
    print(json.dumps({k:a[k] for k in ('classification','candidate','selected_to_second_all_300_bytes_equal','second_to_action_all_300_bytes_equal','event_count')},ensure_ascii=False))
    return a

if __name__=='__main__':run()
