#!/usr/bin/env python3
"""Run exactly one native loss on the scoped successor, retaining all old guards.

The historical controller/validator sources are immutable. Only candidate SHA,
case identity and output location are bound to this explicitly rebuilt successor.
"""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys
import types

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_bp_loss_return_successor as successor
SELF='scripts/pr16_bp_loss_return_native.py'
WORKFLOW='.github/workflows/pr16-bp-loss-return-native.yml'
OUT=ROOT/'.local/pr16-bp-loss-return-native'
OLD='scripts/pr16_bp_battle_return.py'
OLD_SHA='f279ef18c9cde54ed46ffd35bcbcaf51ce6f14edf09f23e22113a811818c25ba'
STATUS='PASS_SCOPED_NATIVE_LOSS_RETURN_NOT_BP'
CASE='factory-loss-return'
SCOPE='PR16_P05_SCOPED_FACTORY_LOSS_RETURN'


def derived_driver():
    import pr16_bp_battle_progress as first
    text=first.checked_text(ROOT/OLD,OLD_SHA)
    replacements=[("SELF='scripts/pr16_bp_battle_return.py'",'SELF='+repr(SELF)),
        ("WORKFLOW='.github/workflows/pr16-bp-battle-return.yml'",'WORKFLOW='+repr(WORKFLOW)),
        ("STATUS='DIAGNOSTIC_FIRST_BATTLE_RETURN_NOT_BP'",'STATUS='+repr(STATUS)),
        ("CASE='first-battle-return'",'CASE='+repr(CASE)),
        ("SCOPE='PR16_P05_FIRST_BATTLE_RETURN'",'SCOPE='+repr(SCOPE)),
        ("ROOT/'.local/pr16-bp-battle-return'","ROOT/'.local/pr16-bp-loss-return-native'"),
        ("paths=[first.OLD_DRIVER,first.OLD_CONTROLLER,first.SELF,first.SOURCE,",
         "paths=["+repr(OLD)+","+repr(successor.SELF)+","+repr(successor.SOURCE)+",'tests/test_pr16_bp_loss_return_successor.py',first.OLD_DRIVER,first.OLD_CONTROLLER,first.SELF,first.SOURCE,")]
    for before,after in replacements:text=first.replace_once(text,before,after)
    module=types.ModuleType('pr16_scoped_factory_loss_return');module.__file__=str(ROOT/OLD)
    exec(compile(text,str(ROOT/OLD),'exec'),module.__dict__)
    return module


def require_loss_witness(row,stderr):
    successor.need(row['battle_outcome']==2 and row['final_party_count']==1
        and row['final_marker']==row['final_snapshot_valid']==row['final_reward_pending']==row['final_streak']==0,
        'scoped loss did not restore original party/ledger')
    pattern=rb'BP_RETURN label=transition frame=(\d+) cb2='+f'{successor.ENTRY:08x}'.encode()+rb' '
    dispatch=re.findall(pattern,stderr)
    successor.need(len(dispatch)==1 and row['outcome_frame']<=int(dispatch[0])<row['facility_return_frame'],
        'bound loss-dispatch callback not observed exactly once')
    successor.need(not re.search(rb'BP_RETURN [^\n]*cb2=08055f65',stderr),'native loss still reached WhiteOut')
    return int(dispatch[0])


def run():
    import pr16_bp_selection_native as launch
    module=derived_driver()
    recipe=successor.run()
    original_layer=launch.previous.layer
    original_sha=launch.SHA
    # Process-local adapter; old modules and files on disk are never rewritten.
    adapter=types.SimpleNamespace(**vars(original_layer))
    adapter.SHA=recipe['candidate']['sha256'];adapter.OUT=successor.OUT;adapter.SELF=successor.SELF
    adapter.run=lambda:recipe
    checked=module.validate
    observed={}
    def validate(raw,stderr,code):
        row=checked(raw,stderr,code)
        observed['dispatch_frame']=require_loss_witness(row,stderr)
        return row
    module.validate=validate
    try:
        launch.previous.layer=adapter
        launch.SHA=adapter.SHA
        report=module.run()
    finally:
        launch.previous.layer=original_layer
        launch.SHA=original_sha
    report.update(successor_recipe=recipe,loss_dispatch=observed,
        historical_native_driver=dict(path=OLD,sha256=OLD_SHA),
        accepted_cancel_replayed=False,ordinary_whiteout_physical_replay=False,
        historical_acceptance_relabelled=False,native_loss_return_accepted=report['status']==STATUS)
    (OUT/'result.json').write_bytes(successor.stable(report))
    # Rebind the changed result bytes; all original source/generated/execution evidence stays intact.
    receipt=json.loads((OUT/'receipt.json').read_bytes())
    receipt['members']['result.json']=successor.identity((OUT/'result.json').read_bytes())
    (OUT/'receipt.json').write_bytes(successor.stable(receipt))
    return report


if __name__=='__main__':
    result=run()
    print(json.dumps({k:result[k] for k in ('status','actual_new_processes','successful_fresh_cores','failures','loss_dispatch')}))
    sys.exit(0 if result['status']==STATUS else 1)
