#!/usr/bin/env python3
"""Read the exact failed candidate's native call sites; not runtime acceptance.

Exports bounded disassembly, pointer preimages and selected row identities only.
No ROM/save is copied to an artifact, mutated, or committed by this command.
"""
from pathlib import Path
import json
import struct
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_integrated_native as native


def calls(raw,start,end,target):
    result=[]
    for off in range(start,end-3,2):
        hi,lo=struct.unpack_from('<HH',raw,off)
        if hi&0xF800!=0xF000 or lo&0xF800!=0xF800:continue
        displacement=((hi&0x7FF)<<12)|((lo&0x7FF)<<1)
        if displacement&0x400000:displacement-=0x800000
        if native.layer.BASE+off+4+displacement==target:
            result.append({'call':hex(native.layer.BASE+off),'return_thumb':hex(native.layer.BASE+off+4|1),
                           'preimage':raw[off:off+4].hex()})
    return result


def run():
    path=ROOT/'.local/pr16-integrated-p07/candidate.gba'
    raw=native.layer.source.checked(path,native.ROM_SHA)
    out=ROOT/'.local/pr16-final-routes/learning-diagnostics';out.mkdir(parents=True,exist_ok=True)
    tables=native.layer.source.RomTables(raw,native.layer.COUNT,selected_species={10,12,13,24})
    report={'status':'BOUNDED_NATIVE_SOURCE_DIAGNOSTIC_NOT_ACCEPTANCE','candidate':native.identity(raw),
            'source_bindings':{p:native.identity((ROOT/p).read_bytes()) for p in ('scripts/pr16_learning_diagnostics.py','scripts/pr16_integrated_native.py')},
            'normal_learn_entry':{'address':'0x0803E1F4','preimage':raw[0x3E1F4:0x3E1FC].hex()},
            'after_evolution_function':'0x09114121',
            'evolution_calls_to_normal_entry':calls(raw,0xCF800,0xD1000,0x0803E1F4),
            'selected_tables':{str(s):{'level':tables.level[s],'egg':tables.egg.get(s,[])} for s in (10,12,13,24)},
            'shared_lucario':native.layer.indexed(raw,native.layer.SHARED_INDEX,native.layer.SHARED_MOVES,13),
            'rom_save_exported':False,'release_ready':False}
    (out/'routing.json').write_bytes(native.stable(report))
    for label,start,end in (('evolution-learning',0x080CF800,0x080D1000),('generic-learning',0x09114060,0x09114200)):
        command=['arm-none-eabi-objdump','-D','-b','binary','-m','arm','-M','force-thumb',
                 '--adjust-vma=0x08000000','--start-address='+hex(start),'--stop-address='+hex(end),str(path)]
        done=subprocess.run(command,check=True,capture_output=True)
        (out/(label+'.asm.txt')).write_bytes(done.stdout)
        native.need(not done.stderr,'unexpected disassembler diagnostic')
    native.layer.source.checked(path,native.ROM_SHA)
    print(json.dumps(report,sort_keys=True))

if __name__=='__main__':run()
