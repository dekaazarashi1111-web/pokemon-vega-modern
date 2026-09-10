#!/usr/bin/env python3
"""Reconcile adopted V4 layers with the exact Stage84 physical consumers.

This is not an adoption of later balance proposals and not native/UI acceptance.
A missing historical row is recorded, never silently unioned into P03.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.modernization_p07_learnsets import _canonical_species_domain, _canonical_move_domain

ROM_SHA = '55cf145e7dd1c8e2568fe9c733b597f8c4bc3d31b7d6fa233a7b4821d1b62c3b'
V4_SHA = '4022cd6e1358f58dffc5ebc38b756166f0a1072f948af6934298f65bd82678b2'
SPECIES_SHA = '4e7cd7ef13761214f506e8ad58611c3dc36a0843b8b6647368677a73613f9366'
MOVES_SHA = 'dba3c65af59ee2dcfa9eecdeeeb1cc189a990b52e27b1878bad6eaec8e104f20'
BASE = 0x08000000
SITES = {'level': 0x4346c, 'egg': 0x45214, 'machine': 0x432b4,
         'tutor': 0x121420, 'machine_moves': 0x1263d8, 'tutor_moves': 0x1213d4}
EXPECTED = {'vega_to_official_historical_adoption': {'level_up':450,'egg':254,'machine':179,'tutor':190},
            'official_to_vega_legacy_preservation': {'level_up':297,'egg':175}}


def need(condition, message):
    if not condition: raise ValueError(message)


def identity(raw): return {'size':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}
def stable(value): return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()
def rows(raw): return list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))


def checked(path, sha):
    need(path.is_file() and not any(p.is_symlink() for p in (path,*path.parents)), 'unsafe input '+str(path))
    raw=path.read_bytes(); need(identity(raw)['sha256']==sha,'input hash differs: '+str(path)); return raw


class RomTables:
    """Bounded readers for existing native table ABIs; no writes or stubs."""
    def __init__(self, raw, species_count=1621, selected_species=None):
        self.raw=raw; self.count=species_count
        self.roots={name:self.u32(site) for name,site in SITES.items()}
        need(self.u32(0x1fda1f8)==self.roots['level'],'level producer/consumer roots differ')
        need(self.u32(0x4528c)==self.roots['egg'],'egg consumer roots differ')
        self.level={}; self.egg={i:[] for i in range(species_count)}
        targets=range(species_count) if selected_species is None else sorted(set(selected_species))
        need(all(type(sid) is int and 0<=sid<species_count for sid in targets),'target species outside table')
        for sid in targets:
            cursor=self.ptr(self.roots['level']+sid*4)
            values=[]
            for _ in range(256):
                off=self.offset(cursor,3); move,level=struct.unpack_from('<HB',raw,off); cursor+=3
                if (move,level)==(0,255): break
                need(0<move<=1063 and 0<=level<=100,f'invalid level row species={sid} address={cursor-3:#x} move={move} level={level}')
                need((move,level) not in values,'duplicate level row')
                values.append((move,level))
            else: raise ValueError('unterminated level table')
            self.level[sid]=values
        cursor=self.roots['egg']; active=None
        for _ in range(50000):
            value=self.u16(cursor); cursor+=2
            if value==65535: break
            if value>=20000:
                active=value-20000;need(active in self.egg,'egg species out of range')
            else:
                need(active is not None and 0<value<=1063,'invalid egg move')
                need(value not in self.egg[active],'duplicate egg move')
                self.egg[active].append(value)
        else: raise ValueError('unterminated egg table')

    def offset(self, address, length):
        off=address-BASE
        need(0<=off<=len(self.raw)-length,'pointer outside ROM')
        return off
    def u32(self, offset):
        need(0<=offset<=len(self.raw)-4,'literal outside ROM')
        return struct.unpack_from('<I',self.raw,offset)[0]
    def ptr(self,address):
        result=self.u32(self.offset(address,4)); self.offset(result,1);return result
    def u16(self,address):return struct.unpack_from('<H',self.raw,self.offset(address,2))[0]
    def check(self,row):
        sid=row['species_id'];move=row['move_id'];route=row['route'];params=row['source_parameters']
        need(type(sid) is int and 0<=sid<self.count,'species outside table')
        if route=='level_up':
            level=int(params['level']); present=(move,level) in self.level[sid]
            return {'present':present,'same_move_other_levels':[lev for mid,lev in self.level[sid] if mid==move and lev!=level]}
        if route=='egg':return {'present':move in self.egg[sid]}
        need(route in ('machine','tutor'),'unsupported route')
        slot=int(params['slot_no']);need(1<=slot<=(128 if route=='machine' else 64),'invalid slot')
        off=self.offset(self.roots[route]+sid*16+(slot-1)//8,1)
        bit=bool(self.raw[off] & (1<<((slot-1)%8)))
        actual=self.u16(self.roots[route+'_moves']+(slot-1)*2)
        return {'present':bit and actual==move,'compatibility_bit':bit,'runtime_slot_move_id':actual,'slot_matches':actual==move}


def recover(v4,species,moves):
    sm={r['species_key']:r for r in rows(species)}; mm={r['move_key']:r for r in rows(moves)}
    selected={name:[] for name in EXPECTED}; selected['official_to_vega_explicit_v4_additions']=[]
    with zipfile.ZipFile(io.BytesIO(v4)) as z:
        names=z.namelist();need(len(names)==len(set(names))==11,'V4 archive inventory differs')
        for n in names:
            need(len(Path(n).parts)==1 and not Path(n).is_absolute() and '\\' not in n,'unsafe V4 member')
        members={n:z.read(n) for n in names}
        need(json.loads(members['VALIDATION_REPORT.json'])['status']=='PASS','V4 validation not PASS')
        for name in ('level_up_final.csv','egg_moves_final.csv','tm_tutor_changes.csv'):
            for line,r in enumerate(rows(members[name]),2):
                s=sm[r['species_key']];m=mm[r['move_key']]
                sd=_canonical_species_domain(s);md=_canonical_move_domain(m)
                added=name=='tm_tutor_changes.csv' or r['source_class']=='V3_ADDED'
                group=None
                if sd=='VEGA_SPECIES' and md=='NORMAL_MOVE' and added:group='vega_to_official_historical_adoption'
                elif sd=='NORMAL_SPECIES' and md=='VEGA_MOVE':group='official_to_vega_explicit_v4_additions' if added else 'official_to_vega_legacy_preservation'
                if group is None:continue
                route='level_up' if name=='level_up_final.csv' else 'egg' if name=='egg_moves_final.csv' else 'machine' if r['slot_type']=='TM' else 'tutor'
                selected[group].append(dict(species_id=int(s['id']),species_key=r['species_key'],form_key=s.get('form_key',''),
                    move_id=int(m['id']),move_key=r['move_key'],route=route,source_csv_line=line,source_member=name,
                    source_class=r.get('source_class','TM_TUTOR_ADDITION'),
                    source_parameters={k:r[k] for k in ('level','order','slot_no','slot_type','slot_key','compatible') if k in r}))
    return selected,{n:identity(raw) for n,raw in sorted(members.items())}


def reconcile(rom,selected):
    targets={r['species_id'] for items in selected.values() for r in items if r['route']=='level_up'}
    tables=RomTables(rom,selected_species=targets);groups={}
    for group,items in selected.items():
        seen=set();out=[]
        for item in items:
            key=(item['source_member'],item['source_csv_line']);need(key not in seen,'duplicate source row');seen.add(key)
            state=tables.check(item);out.append({**item,'rom_observation':state})
        groups[group]={'rows':out,'summary':{'rows':len(out),'present':sum(r['rom_observation']['present'] for r in out),
             'missing':sum(not r['rom_observation']['present'] for r in out),'route_counts':dict(Counter(r['route'] for r in out))}}
    return groups,{k:hex(v) for k,v in tables.roots.items()}


def run(output):
    output=output.absolute();output.resolve().relative_to((ROOT/'.local').resolve())
    need(not any(p.is_symlink() for p in (output,*output.parents)),'unsafe output');output.mkdir(parents=True,exist_ok=True)
    v4=checked(ROOT/'userfile/imports/Pokemon-Vega_MOVE-DISTRIBUTION-V4_IMPLEMENTATION-READY.zip',V4_SHA)
    species=checked(ROOT/'manifests/species_ids.csv',SPECIES_SHA);moves=checked(ROOT/'manifests/move_ids.csv',MOVES_SHA)
    rom=checked(ROOT/'.local/final-integration-candidate/candidate.gba',ROM_SHA)
    selected,members=recover(v4,species,moves)
    (output/'p07-recovered-source.json').write_bytes(stable({'inputs':{'v4':identity(v4),'species':identity(species),'moves':identity(moves)},'source_members':members,'groups':selected}))
    groups,roots=reconcile(rom,selected)
    report=dict(schema_version=1,status='PHYSICAL_TABLE_RECONCILIATION_NOT_NATIVE_ACCEPTANCE',candidate=identity(rom),
                inputs={'v4':identity(v4),'species':identity(species),'moves':identity(moves)},source_members=members,
                groups=groups,roots=roots,rom_changed=False,new_rows_applied=0,full_p07_acceptance=False,release_ready=False,
                retained_source_row_counts_match={k:groups[k]['summary']['route_counts']==v for k,v in EXPECTED.items()},
                limitations=['Table presence is not native acquisition/UI/save acceptance.',
                             'Missing official-species rows must be reconciled with the P03 replacement layer before applying.',
                             'TM/tutor compatibility is not a supply/price/unlock witness.'])
    (output/'p07-reconciliation.json').write_bytes(stable(report))
    print(json.dumps({k:v['summary'] for k,v in groups.items()},ensure_ascii=False))
    need(all(report['retained_source_row_counts_match'].values()),'canonical domains differ from recovered source ledger; inspect rows, do not silently adopt')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-directory',type=Path,default=ROOT/'.local/pr16-continuation/reconciliation')
    try:run(parser.parse_args().output_directory)
    except (OSError,ValueError,KeyError,TypeError,zipfile.BadZipFile) as e:print(str(e),file=sys.stderr);raise SystemExit(1)
