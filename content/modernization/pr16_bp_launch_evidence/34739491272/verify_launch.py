"""Native diagnostic artifact verification; never executes an emulator."""
from __future__ import annotations
import hashlib, io, json, stat, zipfile
from pathlib import PurePosixPath

FORBIDDEN={'.gba','.gb','.gbc','.nds','.sav','.srm','.ips','.ups','.bps','.bin','.exe','.xdelta','.xdelta3'}
SHA='bffd0b83e3724c2fba216052a3ff45afd3ab194ca2168244874746ce0e4a9e92'
def need(value,message):
    if not value:raise ValueError(message)
def identity(data):return {'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def archive(data,*,inner=False):
    files={}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        need(len(z.infolist())==len(set(z.namelist()))<=1000,'duplicate/excess ZIP entries')
        need(sum(i.file_size for i in z.infolist())<=32000000,'ZIP expansion too large')
        for info in z.infolist():
            name=PurePosixPath(info.filename)
            need(not name.is_absolute() and '..' not in name.parts and '\\' not in info.filename and not stat.S_ISLNK(info.external_attr>>16),'unsafe ZIP path')
            if info.is_dir():continue
            need(name.suffix.lower() not in FORBIDDEN and 'private-env' not in name.name,'private payload')
            raw=z.read(info)
            if name.suffix.lower()=='.zip':
                need(not inner,'unexpected nested source ZIP');archive(raw,inner=True)
            elif name.suffix.lower()=='.ppm':
                need(not inner and raw.startswith(b'P6\n240 160\n255\n') and len(raw)==115215,'unbounded PPM')
            else:raw.decode('utf-8');need(b'\0' not in raw,'binary source')
            files[name.as_posix()]=raw
    return files

def verify(data,head):
    files=archive(data)
    prefix='pr16-bp-selection-native/'
    native={k.removeprefix(prefix):v for k,v in files.items() if k.startswith(prefix)}
    report=json.loads(native['result.json']);receipt=json.loads(native['receipt.json'])
    need(receipt['tested_head']==head and report['status']==receipt['status'],'tested HEAD/status differs')
    need(report['candidate']==receipt['candidate']==dict(size=33554432,sha256=SHA),'candidate differs')
    need(set(native)==set(receipt['members'])|{'receipt.json'},'native manifest coverage differs')
    for name,meta in receipt['members'].items():need(identity(native[name])==meta,'member differs: '+name)
    wf='pr16-bp-selection-workflow/'
    need(files[wf+'tested-head.txt'].decode().strip()==head,'entry HEAD differs')
    sources=archive(native['sources.zip'],inner=True)
    need(set(sources)==set(report['sources']),'source coverage differs')
    for name,meta in report['sources'].items():need(identity(sources[name])==meta,'source differs: '+name)
    entries=archive(files[wf+'entry-sources.zip'],inner=True)
    for name,meta in json.loads(files[wf+'entry-bindings.json']).items():need(identity(entries[name])==meta,'entry differs: '+name)
    generated=archive(native['generated-controller.zip'],inner=True)
    need(set(generated)==set(report['generated']),'generated coverage differs')
    for name,meta in report['generated'].items():need(identity(generated[name])==meta,'generated differs: '+name)
    for name in sources:
        if name in entries:need(sources[name]==entries[name],'entry/runtime source differs: '+name)
    for key in ('native_bp_earning_accepted','p05_native_bp_gap_closed','release_ready'):
        need(report[key] is False and receipt[key] is False,'acceptance inflated')
    if report['status']!='FAIL':
        need(report['actual_new_processes']==report['successful_fresh_cores']==len(report['results'])==1,'process count differs')
        need(report['failures']==[],'success with failure')
        need(report['guard_checks']==['bus8','bus16','bus32','raw8','raw16','raw32','register'],'guard set differs')
        case=report['results'][0]['result']['case']
        row=json.loads(native[case+'.stdout']);proc=json.loads(native[case+'.process.json'])
        need(row==report['results'][0]['result'] and proc==report['results'][0]['process'],'stdout/process envelope differs')
        need(proc==dict(schema_version=1,returncode=0,spawn_error=None,timed_out=False),'process did not exit cleanly')
    return dict(archive=identity(data),receipt_members=len(receipt['members']),source_members=len(sources),entry_members=len(entries),generated_members=len(generated),report=report,receipt=receipt,files=files,sources=sources)
