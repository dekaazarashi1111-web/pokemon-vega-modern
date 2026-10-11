#!/usr/bin/env python3
"""固定された実戦開始診断の直後に最初のnative turnを追加。旧sourceは変更しない。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import types

ROOT=Path(__file__).resolve().parents[1]
SELF='scripts/pr16_bp_battle_progress.py'
SOURCE='tools/mgba_pr16_bp_battle_progress.c'
WORKFLOW='.github/workflows/pr16-bp-battle-progress.yml'
OLD_DRIVER='scripts/pr16_bp_selection_native.py'
OLD_CONTROLLER='tools/mgba_pr16_bp_selection_native.c'
DRIVER_SHA='2995799b4e1ac755566f98bee77f01db3ce2439fe931394cf99fc3b5a8d9250c'
CONTROLLER_SHA='7815a29617038dfcd3fd57d9a5a7e61eed0a88c9d4ba7c9b45ec2d1fbc3de690'
STATUS='DIAGNOSTIC_NATIVE_FIRST_TURN_NOT_BP'
CASE='first-native-turn'
SCOPE='PR16_P05_NATIVE_FIRST_TURN'
EXTRA={'move_id','move_slot','pp_before','pp_after','move_menu_frame','move_selected_frame','pp_spent_frame','action_return_frame','player_hp_before','player_hp_after','enemy_hp_before','enemy_hp_after','native_turn_completed'}


def need(ok,message):
    if not ok:raise ValueError(message)


def replace_once(text,before,after):
    need(text.count(before)==1,'derivation anchor changed')
    return text.replace(before,after,1)


def checked_text(path,expected):
    raw=path.read_bytes()
    need(not path.is_symlink() and hashlib.sha256(raw).hexdigest()==expected and b'\0' not in raw,'historical source identity differs')
    return raw.decode('utf-8')


def assemble_controller():
    text=checked_text(ROOT/OLD_CONTROLLER,CONTROLLER_SHA)
    text=replace_once(text,'int main(int argc,char **argv) {',(ROOT/SOURCE).read_text()+'\nint main(int argc,char **argv) {')
    text=replace_once(text,'"second-confirm-battle-probe"','"'+CASE+'"')
    text=replace_once(text,'"PR16_P05_SECOND_CHOOSER_DIAGNOSTIC"','"'+SCOPE+'"')
    text=replace_once(text,'DIAGNOSTIC_SECOND_CONFIRM_BATTLE_ACTION_NOT_BP',STATUS)
    anchor='    a_restore(c,&original);qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);'
    addition=('    struct BPProgress progress=bp_progress(c);\n'
        '    b_copy(c,BP_F(party_snapshot),snapshot,sizeof(snapshot));\n'
        '    bp_require(c,!memcmp(party,snapshot,sizeof(party)) && read8(c,BP_F(snapshot_valid))==1U && read8(c,BP_F(marker))==2U && read32(c,P03_SAVE_COUNTER)==counter,"native turn changed original snapshot or full save counter");\n')
    text=replace_once(text,anchor,addition+anchor)
    anchor='    printf("\\"bp_earned\\":0,'
    addition='    printf("\\"move_id\\":%u,\\"move_slot\\":%u,\\"pp_before\\":%u,\\"pp_after\\":%u,\\"move_menu_frame\\":%u,\\"move_selected_frame\\":%u,\\"pp_spent_frame\\":%u,\\"action_return_frame\\":%u,\\"player_hp_before\\":%u,\\"player_hp_after\\":%u,\\"enemy_hp_before\\":%u,\\"enemy_hp_after\\":%u,\\"native_turn_completed\\":true,",progress.move,progress.slot,progress.before,progress.after,progress.menu,progress.chosen,progress.spent,progress.returned,progress.player_before,progress.player_after,progress.enemy_before,progress.enemy_after);\n'
    return replace_once(text,anchor,addition+anchor)


def validate(raw,stderr,code):
    import pr16_bp_selection_native as launch
    row=launch.previous.fixed.strict_json(raw)
    need(type(row) is dict and EXTRA<=set(row),'native progress fields absent')
    need(row.get('status')==STATUS and row.get('case')==CASE and row.get('scope')==SCOPE,'progress identity differs')
    parent={k:v for k,v in row.items() if k not in EXTRA}
    parent.update(status=launch.STATUS,case=launch.CASE,scope='PR16_P05_SECOND_CHOOSER_DIAGNOSTIC',total_frames=row['action_frame'])
    launch.validate(json.dumps(parent).encode(),stderr,code)
    need(row['native_turn_completed'] is True and all(type(row[k]) is int for k in EXTRA-{'native_turn_completed'}),'native turn fields differ')
    need(type(row['total_frames']) is int and row['action_frame']<row['move_menu_frame']<row['move_selected_frame']<=row['pp_spent_frame']<row['action_return_frame']==row['total_frames']<=row['action_frame']+19000,'native turn frame ordering differs')
    need(0<=row['move_slot']<4 and 0<row['move_id']<=65535 and 0<=row['pp_after']<row['pp_before']<=255 and row['pp_before']-row['pp_after']<=2,'native PP consumption differs')
    need(all(0<=row[k]<=65535 for k in ('player_hp_before','player_hp_after','enemy_hp_before','enemy_hp_after')),'native HP observations differ')
    need(b'BP_PROGRESS move=' in stderr and b'BP_CTRL label=first-turn-return ' in stderr,'native progress trace absent')
    return row


def run():
    sys.path.insert(0,str(ROOT/'scripts'))
    text=checked_text(ROOT/OLD_DRIVER,DRIVER_SHA)
    text=replace_once(text,"generated['controller.c']=(ROOT/SOURCE).read_text();", "generated['controller.c']=assemble_controller();")
    text=replace_once(text,'paths={SELF,SOURCE,WORKFLOW,',"paths={SELF,SOURCE,WORKFLOW,OLD_DRIVER,OLD_CONTROLLER,'tests/test_pr16_bp_battle_progress.py',")
    text=replace_once(text,"report['source_transformations']=transforms;", "transforms.append(dict(source=OLD_CONTROLLER,sha256=CONTROLLER_SHA,extension=SOURCE,scope='APPEND_FIRST_NATIVE_TURN_AFTER_EXACT_LAUNCH_NO_OLD_SOURCE_WRITES'));report['source_transformations']=transforms;")
    module=types.ModuleType('pr16_bp_battle_progress_derived');module.__file__=str(ROOT/OLD_DRIVER)
    module.__dict__.update(assemble_controller=assemble_controller,OLD_DRIVER=OLD_DRIVER,OLD_CONTROLLER=OLD_CONTROLLER,CONTROLLER_SHA=CONTROLLER_SHA)
    exec(compile(text,str(ROOT/OLD_DRIVER),'exec'),module.__dict__)
    module.SELF=SELF;module.SOURCE=SOURCE;module.WORKFLOW=WORKFLOW
    module.OUT=ROOT/'.local/pr16-bp-battle-progress';module.CASE=CASE;module.STATUS=STATUS;module.validate=validate
    report=module.run()
    return report


if __name__=='__main__':
    report=run();print(json.dumps({k:report[k] for k in ('status','actual_new_processes','successful_fresh_cores','failures')}))
    sys.exit(0 if report['status']==STATUS else 1)
