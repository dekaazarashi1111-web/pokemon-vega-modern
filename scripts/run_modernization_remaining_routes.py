#!/usr/bin/env python3
"""Stage84 remaining-route native input probes; never grants whole-phase acceptance."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import run_modernization_p03_fullslots_e2e as base
import modernization_remaining_route_labels as route_labels
import modernization_empty_move_pp_repair as repair

ROM_SHA='09e9d8cf085d175299b58e93347e3beb2467c3c09016130f7d35ce033fa50096'
SEED_SHA='f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb'
SOURCE='tools/mgba_modernization_remaining_routes.c'
SELF='scripts/run_modernization_remaining_routes.py'
SCOPE='P03_FORGET_NATIVE_INPUT_COLD_SAVE_STAGE84'
GUARDS=('bus8','bus16','bus32','raw8','raw16','raw32','register')
EMBED=[('tools/mgba_modernization_p03_archive_ui_e2e.c','remaining_archive.c'),('tools/mgba_modernization_p03_fullslots_e2e.c','p03a_fullslots_embedded.c'),('tools/mgba_modernization_p03_learning_e2e.c','p03_learning_embedded.c'),('tools/mgba_modernization_p02_stage71_acceptance_smoke.c','p03_p02_embedded.c')]

def need(ok,message):
    if not ok: raise ValueError(message)

def cases():
    output=[]
    def add(name,slot=0,action=0,moves=None,pp=None,bonus=228,species=1,after_species=None):
        moves=[33,81,45,52] if moves is None else moves
        pp=[7,8,9,10] if pp is None else pp
        after=moves.copy(); postpp=pp.copy(); postbonus=bonus
        if action==0:
            after=after[:slot]+after[slot+1:]+[0]
            postpp=postpp[:slot]+postpp[slot+1:]+[0]
            postbonus=(bonus & ((1<<(2*slot))-1)) | ((bonus >> (2*(slot+1))) << (2*slot))
        output.append(dict(name=name,slot=slot,action=action,species=species,after_species=after_species or species,moves=moves,pp=pp,bonus=bonus,after=after,after_pp=postpp,after_bonus=postbonus))
    for i in range(4): add('delete-slot-'+str(i),slot=i)
    add('pp-warning-refuse',slot=1,action=1)
    add('confirm-refuse',action=2)
    add('summary-cancel',action=3)
    add('last-move-denied',action=4,moves=[33,0,0,0],pp=[7,0,0,0],bonus=0)
    add('blade-denied',action=5,moves=[768,81,45,52],bonus=0)
    add('bash-denied',action=5,moves=[769,81,45,52],bonus=0)
    add('hm-surf-delete',moves=[57,81,45,52],bonus=0)
    add('keldeo-form-revert',moves=[619,33,45,57],bonus=27,species=938,after_species=881)
    return output

def expected(c,rom_sha=ROM_SHA):
    return dict(schema_version=1,status='PASS',scope=SCOPE,case=c['name'],rom_sha256=rom_sha,
                species_before=c['species'],species_after=c['after_species'],moves_before=c['moves'],moves_after=c['after'],
                pp_before=c['pp'],pp_after=c['after_pp'],bonuses_before=c['bonus'],bonuses_after=c['after_bonus'],
                slot=c['slot'],action=c['action'],host_write_barriers=3,core_instances=2,save_counter_delta=1,
                party_mon_bytes_preserved=100,normal_save_menu=True,fresh_core_continue=True,
                mgba_version='0.10.2',warnings_errors=0,full_p03_acceptance=False,full_p05_acceptance=False,release_ready=False)

def validate(raw,c,process,stderr=b'',rom_sha=ROM_SHA):
    need(base.require_exited(process)==0,'native process failed')
    need(b'mGBA[' not in stderr,'emulator warning/error')
    r=base.strict_json(raw);e=expected(c,rom_sha)
    need(type(r) is dict and set(r)==set(e)|{'witness'},'result schema differs')
    for k,v in e.items(): need(base.same_typed(r[k],v),'result mismatch: '+k)
    w=r['witness'];keys={'bag','mode','party','summary','selection','warning','confirm','denied','deleted','field'}
    need(type(w) is dict and set(w)==keys,'witness schema differs')
    need(all(type(v) is int and 0<=v<24000 for v in w.values()),'witness type/bounds')
    need(0<w['bag']<w['mode']<w['party']<w['field'],'native route ordering')
    need(all(v<w['field'] for k,v in w.items() if k!='field'),'post-field event')
    a=c['action'];summary=a!=4
    need(bool(w['summary'])==summary and bool(w['selection'])==summary,'summary/selection missing')
    if summary: need(w['party']<w['summary']<=w['selection']<w['field'],'summary ordering')
    warning=a not in (3,4,5) and ((c['bonus']>>(2*c['slot']))&3)!=0
    need(bool(w['warning'])==warning,'PP Up warning contract')
    if warning: need(w['selection']<w['warning']<w['field'],'warning ordering')
    need(bool(w['confirm'])==(a in (0,2)),'confirm contract')
    if w['confirm']: need(w['selection']<w['confirm'] and (not warning or w['warning']<w['confirm']),'confirm ordering')
    need(bool(w['denied'])==(a in (4,5)),'denial contract')
    if w['denied']: need(w['party']<w['denied'] and (a!=5 or w['selection']<w['denied']),'denial ordering')
    need(bool(w['deleted'])==(a==0),'delete witness contract')
    if a==0: need(w['confirm']<w['deleted']<w['field'],'delete ordering')
    return r

def embed(text,entry):
    need(len(re.findall(r'\bint\s+main\s*\(',text))==1,'ambiguous embedded main')
    return re.sub(r'\bint\s+main\s*\(','int '+entry+'(',text,count=1)

def header(rows,labels):
    texts=['text_pp_up_warning','text_forget_confirm','text_forgot','text_last_move','text_form_rejected']
    out=[]
    for t in texts:
        a=labels[t];need(type(a) is int and 0x08000000<=a<0x0a000000,'text label outside ROM')
        out.append('#define R_'+t.upper()+' '+hex(a)+'U')
    def arr(a):return '{'+','.join(map(str,a))+'}'
    out.append('static const struct RCase R_CASES[]={')
    for c in rows:
        out.append('{'+','.join([json.dumps(c['name']),str(c['species']),str(c['after_species']),str(c['slot']),str(c['action']),arr(c['moves']),arr(c['pp']),str(c['bonus']),arr(c['after']),arr(c['after_pp']),str(c['after_bonus'])])+'},')
    return '\n'.join(out+['};',''])

def select_cases(rows,selected):
    items=list(enumerate(rows))
    if selected is not None:
        items=[(i,c) for i,c in items if c['name']==selected]
        need(len(items)==1,'unknown or duplicate case')
    return items

def run(out,jobs=2,selected=None):
    out=out.absolute();relative=out.resolve().relative_to((ROOT/'.local').resolve());need(bool(relative.parts),'unsafe output root')
    q=out
    while q!=ROOT: need(not q.is_symlink(),'symlink output');q=q.parent
    out.mkdir(parents=True,exist_ok=True)
    need(not (out/'result.json').is_symlink(),'symlink result');(out/'result.json').unlink(missing_ok=True)
    need(type(jobs) is int and 1<=jobs<=4,'jobs must be 1..4')
    rows=cases();items=select_cases(rows,selected)
    rom=ROOT/'.local/stage83-decided-species/candidate.gba';seed=ROOT/'.local/60_wild_species_root_repair.srm'
    identity=base.identity
    rid={'size':33554432,'sha256':ROM_SHA};sid={'size':131072,'sha256':SEED_SHA}
    need(identity(rom)==rid and identity(seed)==sid,'ROM/seed identity mismatch')
    cfg=base.strict_json((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_bytes())
    d=next(d for d in cfg['domains'] if d['id']=='p02')
    paths={SOURCE,SELF,'tests/test_modernization_remaining_routes.py','.github/workflows/p03-p05-remaining-e2e.yml','scripts/run_modernization_p03_fullslots_e2e.py','config/modernization_stage79_cumulative_mgba.json','config/active_play_baseline.json','design/active_play_baseline.md','infra/toolchain_manifest.json','infra/setup_github_actions.sh','tools/modernization_remaining_route_labels.py','tools/modernization_empty_move_pp_repair.py','manifests/move_ids.csv'}
    paths.update(x for x,_ in EMBED)
    for p in (d['runner'],*d['dependencies']):
        need(identity(ROOT/p['path'])=={k:p[k] for k in ('size','sha256')},'inherited harness changed: '+p['path']);paths.add(p['path'])
    binding={p:identity(ROOT/p) for p in sorted(paths)}
    stamps={p:(ROOT/p).stat().st_mtime_ns for p in sorted(paths)}
    import csv
    sentinel=[x for x in csv.DictReader((ROOT/'manifests/move_ids.csv').read_text().splitlines()) if x['move_key']=='MOVE_KEY_NONE']
    need(len(sentinel)==1 and sentinel[0]['id']=='0','MOVE_NONE manifest identity differs')
    child,recipe=repair.build(rom.read_bytes())
    child_sha=recipe['candidate']['sha256']
    (out/'candidate.json').write_text(json.dumps(recipe,sort_keys=True,indent=2)+'\n')
    labels=route_labels.resolve(child)
    (out/'route-labels.json').write_text(json.dumps(labels,sort_keys=True,indent=2)+'\n')
    _,_,p=base.capture(['bash','infra/setup_github_actions.sh','--check'],out/'fixed-toolchain',120);need(base.require_exited(p)==0,'fixed toolchain check failed')
    results=[]
    try:
        with tempfile.TemporaryDirectory(prefix='remaining-routes-',dir=ROOT/'.local') as td:
            w=Path(td)
            for src,dst in EMBED:(w/dst).write_text(embed((ROOT/src).read_text(),'old_'+Path(dst).stem))
            (w/'remaining_vectors.h').write_text(header(rows,labels))
            candidate=w/'candidate.gba';candidate.write_bytes(child);candidate.chmod(0o444)
            binary=w/'runner'
            _,_,p=base.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(w),SOURCE,'-lmgba','-o',str(binary)],out/'compile',120)
            need(base.require_exited(p)==0,'strict C compile failed')
            for api in GUARDS:
                raw,err,p=base.capture([str(binary),'--guard-check',api],out/('guard-'+api),10)
                need(base.require_exited(p)==1 and not raw and err==b'P03 archive: host write after observation barrier\n','write guard failed: '+api)
            control=w/'parent-negative.srm';shutil.copyfile(seed,control)
            raw,err,p=base.capture([str(binary),str(rom),str(control),ROM_SHA,SEED_SHA,'0'],out/'parent-negative',240)
            need(base.require_exited(p)==1 and not raw and b'slot=3 move=0/0 pp=35/0\n' in err and err.endswith(b'P03 archive: forget move/PP differs\n'),'Stage83 defect control did not reproduce')
            def one(item):
                i,c=item;save=w/(c['name']+'.srm');shutil.copyfile(seed,save)
                raw,err,p=base.capture([str(binary),str(candidate),str(save),child_sha,SEED_SHA,str(i)],out/c['name'],240)
                try: result=validate(raw,c,p,err,child_sha);error=None
                except (ValueError,KeyError,TypeError) as e:result=None;error=str(e)
                return dict(name=c['name'],process=p,result=result,validation_error=error,stdout=identity(out/(c['name']+'.stdout')),stderr=identity(out/(c['name']+'.stderr')))
            with ThreadPoolExecutor(max_workers=jobs) as pool:results=list(pool.map(one,items))
            (out/'matrix-outcomes.json').write_text(json.dumps(results,sort_keys=True,indent=2)+'\n')
            need(all(x['validation_error'] is None for x in results),'failed cases: '+', '.join(x['name']+': '+str(x['validation_error']) for x in results if x['validation_error'] is not None))
            need(identity(candidate)==recipe['candidate'],'private candidate modified')
    finally:
        need(identity(rom)==rid and identity(seed)==sid,'ROM/seed modified')
        need(binding=={p:identity(ROOT/p) for p in paths},'source/baseline modified')
        need(stamps=={p:(ROOT/p).stat().st_mtime_ns for p in paths},'source/baseline timestamps changed')
    report=dict(schema_version=1,status='PASS',scope=SCOPE,candidate_stage=84,rom=recipe['candidate'],parent_rom=rid,recipe=recipe,seed=sid,source_bindings=binding,
                cases=results,guard_checks=list(GUARDS),fresh_processes=len(results),core_instances=2*len(results),parent_negative_controls=1,cache_reuse=0,
                validation_class='FIXED_TOOLCHAIN_NATIVE_EXECUTION',full_matrix=selected is None,full_p03_acceptance=False,
                full_p05_acceptance=False,release_ready=False,active_baseline_changed=False,
                fixture_scope='Party/position/items configured before Bag input; no natural acquisition claim')
    (out/'result.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-directory',type=Path,default=ROOT/'.local/remaining-routes');p.add_argument('--jobs',type=int,default=2);p.add_argument('--case')
    a=p.parse_args()
    try:
        r=run(a.output_directory,a.jobs,a.case);print(json.dumps({k:v for k,v in r.items() if k not in ('cases','source_bindings')},indent=2));return 0
    except (ValueError,OSError,KeyError) as e:print('remaining routes: '+str(e),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
