#!/usr/bin/env python3
"""Connect the two real evolution callers to the accepted level-0 consumer.

The exact failed candidate remains the immutable parent. Only its normal-entry
veneer and one allocator-owned 40-byte dispatcher change. Other callers tail
jump to the existing QoL adapter, preserving its behavior and the incoming LR.
No table, monster, save, facility flag, or acceptance result is rewritten.
"""
from pathlib import Path
import argparse
import json
import struct
import subprocess
import sys
import tempfile
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import pr16_p07_preserved_layer as layer
need=layer.need
identity=layer.identity
stable=layer.stable
PARENT_SHA='beef0d6aaf5b9e1be04b3075a7e9a4f388110776763fa11c6a74fdc6a38310c7'
ROM_SIZE=33554432
ENTRY=0x3E1F4
ENTRY_PREIMAGE=bytes.fromhex('004b184729773709')
CALLS=((0xCFEF4,bytes.fromhex('6ef77ef9')),(0xD0A68,bytes.fromhex('6df7c4fb')))
NORMAL=0x09377729
EVOLUTION=0x09114121
EVOLUTION_PREIMAGE=bytes.fromhex('8446f8b562465423')
START=0x15DDCB0
ASM='overlays/modernization_p03_evolution_learning/dispatch.s'
SELF='scripts/pr16_evolution_learning_repair.py'
DISPATCH=bytes.fromhex('7246054b9a4204d0044b9a4201d0044b1847044b1847c046f9fe0c086d0a0d082977370921411109')


def verify_sites(parent):
    need(len(parent)==ROM_SIZE,'evolution parent size differs')
    need(parent[ENTRY:ENTRY+8]==ENTRY_PREIMAGE,'normal-entry preimage differs')
    for off,raw in CALLS:need(parent[off:off+4]==raw,'evolution caller preimage differs: '+hex(off))
    off=EVOLUTION-layer.BASE-1
    need(parent[off:off+8]==EVOLUTION_PREIMAGE,'evolution consumer preimage differs')
    need(parent[START:START+len(DISPATCH)]==b'\xff'*len(DISPATCH),'dispatcher allocation is not empty')


def patch_sites(parent):
    verify_sites(parent)
    candidate=bytearray(parent)
    candidate[ENTRY:ENTRY+8]=layer.veneer(8,layer.BASE+START)
    candidate[START:START+len(DISPATCH)]=DISPATCH
    cursor=0
    for off,size in ((ENTRY,8),(START,len(DISPATCH))):
        need(candidate[cursor:off]==parent[cursor:off],'undeclared evolution-repair change')
        cursor=off+size
    need(candidate[cursor:]==parent[cursor:],'undeclared evolution-repair trailing change')
    return bytes(candidate)


def allocation(parent,layout):
    need(layout['schema_version']==1 and len(layout['allocations'])==85,'P07 parent allocation differs')
    requests=[]
    for i,row in enumerate(layout['allocations']):
        need(row['sequence']==i and row['end_exclusive']==row['start']+row['size'],'allocation sequence/span differs')
        need(identity(parent[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'parent allocation content changed')
        requests.append({k:row[k] for k in ('name','region','size','alignment','start','owner','purpose','content_sha256')})
    requests.append({'name':'modernization-p03-native-evolution-dispatch','region':'integration_modules',
                     'size':len(DISPATCH),'alignment':4,'owner':'P03','purpose':'two real evolution callers use accepted level-0 learning',
                     'content_sha256':identity(DISPATCH)['sha256']})
    layer.source.checked(ROOT/'config/rom_regions.csv',layer.REGIONS_SHA)
    plan=layer.build_allocation_report_from_csv(ROOT/'config/rom_regions.csv',requests)
    need(plan['summaries']['overlap_count']==0 and plan['allocations'][-1]['start']==START,'unexpected dispatch allocation')
    return plan


def verify_assembly():
    with tempfile.TemporaryDirectory(prefix='pr16-evo-asm-',dir=ROOT/'.local') as name:
        work=Path(name)
        subprocess.run(['arm-none-eabi-as','-mcpu=arm7tdmi','-mthumb',str(ROOT/ASM),'-o',str(work/'dispatch.o')],check=True,capture_output=True)
        subprocess.run(['arm-none-eabi-objcopy','-O','binary','-j','.text',str(work/'dispatch.o'),str(work/'dispatch.bin')],check=True,capture_output=True)
        need((work/'dispatch.bin').read_bytes()==DISPATCH,'assembly differs from reviewed exact Thumb dispatch')


def build(parent,layout):
    need(identity(parent)=={'size':ROM_SIZE,'sha256':PARENT_SHA},'exact failed P07 candidate required')
    verify_sites(parent)
    plan=allocation(parent,layout)
    candidate=patch_sites(parent)
    return candidate,{'schema_version':1,'status':'BUILT_NOT_NATIVE_ACCEPTED','parent':identity(parent),'candidate':identity(candidate),
        'crc32':f'{zlib.crc32(candidate)&0xffffffff:08X}','allocation':plan,
        'cause':'both native evolution scenes called the ordinary level-only QoL delegate instead of the accepted level-0 consumer',
        'normal_delegate_preserved':hex(NORMAL),'after_evolution_consumer':hex(EVOLUTION),
        'native_call_sites':[{'address':hex(layer.BASE+off),'return_thumb':hex(layer.BASE+off+5),'preimage':raw.hex()} for off,raw in CALLS],
        'writes':[{'offset':ENTRY,'before':identity(ENTRY_PREIMAGE),'after':identity(candidate[ENTRY:ENTRY+8])},
                  {'offset':START,'before':identity(b'\xff'*len(DISPATCH)),'after':identity(DISPATCH)}],
        'move_table_changes':0,'save_layout_changes':0,'active_baseline_changed':False,'native_acceptance':False,'release_ready':False}


def run(output):
    output=output.absolute();output.resolve().relative_to((ROOT/'.local').resolve())
    need(not any(p.is_symlink() for p in (output,*output.parents)),'unsafe repair output')
    output.mkdir(parents=True,exist_ok=True)
    source=ROOT/'.local/pr16-integrated-p07/candidate.gba'
    parent=layer.source.checked(source,PARENT_SHA)
    parent_report=json.loads((source.with_suffix('.json')).read_bytes())
    need(parent_report['candidate']==identity(parent),'parent recipe does not identify the failed candidate')
    verify_assembly();candidate,report=build(parent,parent_report['allocation'])
    (output/'candidate.gba').write_bytes(candidate)
    for name,left,right in (('integrated-p07-to-evolution-repaired.bps',parent,candidate),('evolution-repaired-to-integrated-p07.bps',candidate,parent)):
        patch=layer.create_bps(left,right);need(layer.apply_bps(left,patch)==right,'repair BPS round trip failed')
        (output/name).write_bytes(patch)
    report['source_bindings']={p:identity((ROOT/p).read_bytes()) for p in (SELF,ASM,'tools/rom_allocator.py','config/rom_regions.csv')}
    report['patches']={p.name:identity(p.read_bytes()) for p in sorted(output.glob('*.bps'))}
    (output/'candidate.json').write_bytes(stable(report))
    need(identity(source.read_bytes())==identity(parent),'P07 parent overwritten')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'.local/pr16-evolution-repair')
    try:print(json.dumps(run(p.parse_args().output),ensure_ascii=False))
    except (ValueError,OSError,KeyError,TypeError,subprocess.CalledProcessError) as e:
        if isinstance(e,subprocess.CalledProcessError) and e.stderr:print(e.stderr.decode(),file=sys.stderr)
        print(str(e),file=sys.stderr);raise SystemExit(1)
