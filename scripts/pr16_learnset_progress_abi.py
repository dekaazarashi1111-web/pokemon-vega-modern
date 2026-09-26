#!/usr/bin/env python3
"""既存ROM入口の限定診断。host試験/ARMコンパイル/nativeは行わない。"""
import hashlib
import json
import os
import struct
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_learnset_progress_verify as p

p.current_pr(os.environ['GITHUB_SHA'])
p.WORK.mkdir(parents=True, exist_ok=True)
(p.WORK/'proof').mkdir()
try:
    p.restore()
except ValueError as exc:
    if str(exc) != '既存GiveMoveToBoxMon hook不一致':
        raise
raw=(p.WORK/'parent.gba').read_bytes()
p.need(p.identity(raw)==p.s.read_json(p.ROOT/p.CP)['candidate'], '固定ROM不一致')
regions={}
for name,start,end in (('legacy',0x3DF80,0x3E350),('cfru',0x1114200,0x11149A0)):
    source=p.WORK/(name+'.bin')
    source.write_bytes(raw[start:end])
    out=subprocess.check_output(['arm-none-eabi-objdump','-D','-b','binary','-m','arm',
        '--disassembler-options=force-thumb','--adjust-vma='+str(p.BASE+start),str(source)])
    (p.WORK/'proof'/(name+'.txt')).write_bytes(out.replace(str(p.ROOT).encode(),b'$REPO'))
    regions[name]={'offset':start,'size':end-start,'sha256':hashlib.sha256(raw[start:end]).hexdigest()}
entries={hex(at):raw[at:at+16].hex() for at in (0x3D1C0,0x3DF9C,0x3E008,0x3E01C,0x3E14C,0x3E174,0x3E1F4,0x1114538,0x11145F0)}
p.write(p.WORK/'proof/abi-inspection.json',{'status':'DIAGNOSTIC_ONLY_NOT_ACCEPTANCE',
    'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
    'candidate':p.identity(raw),'regions':regions,'entries':entries,
    'new_host_tests':0,'arm_compiles':0,'native_runs':0})
