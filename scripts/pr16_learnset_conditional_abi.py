#!/usr/bin/env python3
"""保存候補の入口とbranch veneerだけを採取。host/ARM/nativeは実行しない。"""
from __future__ import annotations
import json
import os
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_learnset_conditional_host as h
from pr16_learnset_payload_verify import current_pr
from tools import pr16_learnset_successor as s
WORK=ROOT/'.local/pr16-learnset-conditional-abi'


def inspect(raw, at):
    result={'offset':at,'address':0x08000000+at,'preimage':raw[at:at+32].hex()}
    if raw[at:at+4] == bytes.fromhex('004b1847'):
        target=struct.unpack_from('<I',raw,at+4)[0]
        result['thumb_veneer_target']=target
        pos=(target&~1)-0x08000000
        h.need(0<=pos<=len(raw)-32,'veneer target outside ROM')
        result['target_preimage']=raw[pos:pos+64].hex()
    return result


def main():
    current_pr(os.environ['GITHUB_SHA'])
    WORK.mkdir(parents=True);h.WORK=WORK/'restore';h.WORK.mkdir()
    raw,reports=h.restore_progress()
    entries={name:inspect(raw,at) for name,at in (
        ('evolution',0x1114120),('reminder',0x11141D4),('egg',0x451EC),('all_egg',0x10EB970),
        ('native_relearner',0x432D0),('archive_delegate',0x154B280))}
    out=WORK/'proof';out.mkdir()
    report={'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
        'candidate':h.old.saved.identity(raw),'entries':entries,'old_arm_compiles':0,
        'new_native_runs':0,'accepted_tests_rerun':0,'scope':'READ_ONLY_SAVED_ROM_ABI_NOT_ACCEPTANCE',
        'parents':{k:v['candidate'] for k,v in reports.items()}}
    (out/'abi.json').write_bytes(s.encode(report))
    print(json.dumps(report))


if __name__=='__main__':main()
