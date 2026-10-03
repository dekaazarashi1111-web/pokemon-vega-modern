#!/usr/bin/env python3
"""初回turnの固定診断を前置条件にし、未観測の1戦勝敗・施設帰還だけを追加する。"""
from __future__ import annotations
import json
from pathlib import Path
import sys
import types

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_bp_battle_progress as first
need,replace_once,checked_text=first.need,first.replace_once,first.checked_text
SELF='scripts/pr16_bp_battle_return.py'
SOURCE='tools/mgba_pr16_bp_battle_return.c'
WORKFLOW='.github/workflows/pr16-bp-battle-return.yml'
STATUS='DIAGNOSTIC_FIRST_BATTLE_RETURN_NOT_BP'
CASE='first-battle-return'
SCOPE='PR16_P05_FIRST_BATTLE_RETURN'
PINS={
    first.SELF:'59f7716a2eee46df96190f0e6511ca180aea11aac28f7c6efe529b19f7c1b24c',
    first.SOURCE:'37b6581d714cf47e605b0516215456415e1787f03a9af830cc7ce441657a173b',
}
EXTRA={'return_start_frame','additional_turns','forced_switches','additional_pp_events',
       'battle_outcome','outcome_frame','facility_return_frame','final_party_count',
       'final_marker','final_snapshot_valid','final_reward_pending','final_streak',
       'final_script_pointer','final_callback2','native_afterbattle_observed',
       'original_party_or_snapshot_bytes_verified'}


def assemble_controller():
    for name,sha in PINS.items():checked_text(ROOT/name,sha)
    text=first.assemble_controller()
    text=replace_once(text,'int main(int argc,char **argv) {',
                      (ROOT/SOURCE).read_text()+'\nint main(int argc,char **argv) {')
    text=replace_once(text,'"'+first.CASE+'"','"'+CASE+'"')
    text=replace_once(text,'"'+first.SCOPE+'"','"'+SCOPE+'"')
    text=replace_once(text,first.STATUS,STATUS)
    anchor='    a_restore(c,&original);qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);'
    text=replace_once(text,anchor,'    struct BPReturn finish=br_battle_return(c,party,counter);\n'+anchor)
    anchor='    printf("\\"bp_earned\\":0,'
    fields=['return_start_frame','additional_turns','forced_switches','additional_pp_events',
            'battle_outcome','outcome_frame','facility_return_frame','final_party_count',
            'final_marker','final_snapshot_valid','final_reward_pending','final_streak',
            'final_script_pointer','final_callback2']
    args=['start','turns','switches','pp_events','outcome','outcome_frame','facility_frame',
          'final_count','marker','snapshot','pending','streak','script','callback2']
    fmt=''.join('\\"'+name+'\\":%u,' for name in fields)
    fmt+='\\"native_afterbattle_observed\\":true,\\"original_party_or_snapshot_bytes_verified\\":600,'
    addition='    printf("'+fmt+'",'+','.join('finish.'+a for a in args)+');\n'
    return replace_once(text,anchor,addition+anchor)


def validate(raw,stderr,code):
    import pr16_bp_selection_native as launch
    row=launch.previous.fixed.strict_json(raw)
    need(type(row) is dict and EXTRA<=set(row),'battle return fields absent')
    need(row.get('status')==STATUS and row.get('scope')==SCOPE and row.get('case')==CASE,'return identity differs')
    parent={k:v for k,v in row.items() if k not in EXTRA}
    parent.update(status=first.STATUS,scope=first.SCOPE,case=first.CASE,total_frames=row['action_return_frame'])
    first.validate(json.dumps(parent).encode(),stderr,code)
    need(row['native_afterbattle_observed'] is True,'AfterBattle absent')
    need(all(type(row[k]) is int for k in EXTRA-{'native_afterbattle_observed'}),'return integer fields differ')
    need(type(row['total_frames']) is int and row['return_start_frame']==row['action_return_frame']
         <row['outcome_frame']<=row['facility_return_frame']==row['total_frames']
         <=row['return_start_frame']+90000,'return frame ordering differs')
    need(1<=row['additional_turns']<=48 and 0<=row['forced_switches']<=2
         and 0<=row['additional_pp_events']<=row['additional_turns'],'return input counts differ')
    need(row['original_party_or_snapshot_bytes_verified']==600,'original party restoration/snapshot not verified')
    expected={1:(3,2,1,1,1),2:(1,0,0,0,0)}
    need(row['battle_outcome'] in expected,'return accepted an outcome other than win/loss')
    actual=tuple(row[k] for k in ('final_party_count','final_marker','final_snapshot_valid','final_reward_pending','final_streak'))
    need(actual==expected[row['battle_outcome']],'AfterBattle ledger differs from native outcome')
    need(0x08000000<=row['final_script_pointer']<0x0A000000 and 0x08000000<row['final_callback2']<0x0A000000,'return callback/script invalid')
    need(b'BP_RETURN label=extension-start ' in stderr and b'BP_RETURN label=facility-stop ' in stderr,'return trace absent')
    return row


def run():
    for name,sha in PINS.items():checked_text(ROOT/name,sha)
    text=checked_text(ROOT/first.OLD_DRIVER,first.DRIVER_SHA)
    text=replace_once(text,"generated['controller.c']=(ROOT/SOURCE).read_text();","generated['controller.c']=assemble_controller();")
    paths=[first.OLD_DRIVER,first.OLD_CONTROLLER,first.SELF,first.SOURCE,
           'tests/test_pr16_bp_battle_progress.py','tests/test_pr16_bp_battle_return.py',
           'overlays/facility_runtime/facility_runtime.c','overlays/facility_runtime/facility_runtime.h']
    text=replace_once(text,'paths={SELF,SOURCE,WORKFLOW,','paths={SELF,SOURCE,WORKFLOW,'+','.join(repr(p) for p in paths)+',')
    text=replace_once(text,"scope='SECOND_CONFIRM_DIAGNOSTIC_NOT_EARNING'","scope='FIRST_BATTLE_RETURN_DIAGNOSTIC_NOT_EARNING'")
    text=replace_once(text,"report['source_transformations']=transforms;", "transforms.append(dict(source=FIRST_SOURCE,sha256=PINS[FIRST_SOURCE],extension=SOURCE,scope='APPEND_FIRST_BATTLE_RETURN_WITHOUT_OLD_SOURCE_OR_ROM_WRITES'));report['source_transformations']=transforms;")
    module=types.ModuleType('pr16_bp_battle_return_derived');module.__file__=str(ROOT/first.OLD_DRIVER)
    module.__dict__.update(assemble_controller=assemble_controller,FIRST_SOURCE=first.SOURCE,PINS=PINS)
    exec(compile(text,str(ROOT/first.OLD_DRIVER),'exec'),module.__dict__)
    module.SELF=SELF;module.SOURCE=SOURCE;module.WORKFLOW=WORKFLOW
    module.OUT=ROOT/'.local/pr16-bp-battle-return';module.CASE=CASE;module.STATUS=STATUS;module.validate=validate
    return module.run()


if __name__=='__main__':
    report=run();print(json.dumps({k:report[k] for k in ('status','actual_new_processes','successful_fresh_cores','failures')}))
    sys.exit(0 if report['status']==STATUS else 1)
