#!/usr/bin/env python3
"""START保存に限定したvalid-live Flash失敗の非破壊error gate。"""
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_save_failure as old
need,identity=old.need,old.identity
SOURCE='overlays/dex_owner/dex_start_save_failure.S'
BINDINGS='content/modernization/pr16_dex_start_failure_bindings.json'
CP='content/modernization/pr16_dex_save_failure_checkpoint.json'
def checkpoint():return json.loads((ROOT/CP).read_bytes())
def proof():return json.loads((ROOT/BINDINGS).read_bytes())
def link(folder):
 previous=old.SOURCE
 try:old.SOURCE=SOURCE;return old.link(folder)
 finally:old.SOURCE=previous
def apply(before,accepted,payload,linked):
 cp=checkpoint();need(identity(accepted)==cp['candidate'],'exact invalid-live accepted parent')
 for row in proof()['windows']:
  at=row['address']-0x08000000;need(identity(before[at:at+row['size']])==dict(size=row['size'],sha256=row['sha256']),'signed START callback '+row['id'])
 after,placed=old.apply(before,payload,linked)
 allocation=cp['updated_gates']['measurement']['placement']['allocation']
 need(len(allocation['allocations'])==111,'exact prior111 owners')
 old.b.preserve_allocated_owners(accepted,after,dict(allocations=allocation['allocations'][:-1]))
 lease=allocation['allocations'][-1];need(lease['name']=='pr16_dex_save_failure_gates'and lease['gba_start']==old.BASE,'explicit replacement of failure owner only')
 windows=[(old.BASE-0x08000000,old.END-0x08000000),(0xDB360,0xDB368),(0xF64A8,0xF64B0)]
 cursor=0
 for a,z in sorted(windows):need(accepted[cursor:a]==after[cursor:a],'all non-lease parent bytes preserved');cursor=z
 need(accepted[cursor:]==after[cursor:],'whole parent suffix retained')
 placed.update(replaced_owner=lease['name'],all110_other_owners_byte_identical=True,start_callback=0x0806F131,start_modes=[0,4],other_valid_failure_paths_changed=False,automatic_wipe_retry_accepted=False)
 return after,placed
