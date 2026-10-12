#!/usr/bin/env python3
"""型付き図鑑APIを保ち、ROM用lookupを完全同値なrun/literal表へ縮小する。"""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
import pr16_dex_namespace as ns
import pr16_dex_adapter_tables as original
ROOT=Path(__file__).resolve().parents[1]
ADAPTER_SOURCE='overlays/dex_owner/dex_adapter.c'
ADAPTER_SHA256='aa4ac552bcb0b4cb768c54b840240822db4e5038e1e7577558bbc34c86c361f2'
TABLE='overlays/dex_owner/dex_compact_tables.h'
ADAPTER='overlays/dex_owner/dex_compact_adapter.c'
META='content/modernization/pr16_dex_compact_mapping.json'
CONST=0x8000;LITERAL=0x4000;VALUE=0x3FFF

def encode(values,literals_allowed=True):
    ns.need(values and all(type(v)is int and 0<=v<=VALUE for v in values),'bounded nonempty u14 sequence')
    length=len(values);ns.need(length<=65536,'u16 keys')
    costs=[0]*(length+1);choices=[None]*length
    for start in range(length-1,-1,-1):
        best=(1<<30,0,0)
        for slope in (0,1):
            for end in range(start,length):
                if values[end]!=values[start]+(end-start)*slope:break
                best=min(best,(4+costs[end+1],end+1,slope))
        if literals_allowed:
            for end in range(start+1,length+1):
                best=min(best,(4+2*(end-start)+costs[end],end,2))
        costs[start],end,kind=best;choices[start]=(end,kind)
    runs=[];literals=[];start=0
    while start<length:
        end,kind=choices[start]
        if kind==2:
            literals.extend(values[start:end]);ns.need(len(literals)<=VALUE+1,'literal index width')
            value=(len(literals)-1)|LITERAL
        else:value=values[end-1]|(CONST if kind==0 else 0)
        runs.append((end-1,value));start=end
    validate(runs,literals,values)
    return runs,literals

def decode(key,runs,literals):
    if key<0 or key>runs[-1][0]:return 0
    lo,hi=0,len(runs)
    while lo<hi:
        mid=(lo+hi)//2
        if runs[mid][0]<key:lo=mid+1
        else:hi=mid
    end,tag=runs[lo];value=tag&VALUE
    if not tag&CONST:value-=end-key
    return literals[value] if tag&LITERAL else value

def validate(runs,literals,values):
    start=0
    for end,tag in runs:
        ns.need(start<=end<len(values) and tag&0xC000!=0xC000,'ordered disjoint valid run')
        value=tag&VALUE
        if tag&LITERAL:ns.need(end-start<=value<len(literals),'literal endpoints inside array')
        elif not tag&CONST:ns.need(value>=end-start,'affine subtraction cannot underflow')
        start=end+1
    ns.need(start==len(values),'complete domain')
    ns.need([decode(i,runs,literals)for i in range(len(values))]==values,'lossless compact mapping')

def mappings():
    n=ns.build();species=[x['owner']for x in n['species']]+[original.extension(n)['owner']]
    owners=n['official_national_to_owner'];representatives=[0]*1207
    for sid,owner in enumerate(species):
        if owner and not representatives[owner]:representatives[owner]=sid
    ns.need([representatives[o]for o in owners]==n['official_national_to_representative_sid'],'lowest SID is existing stable representative for all1025')
    mask=bytearray(151)
    for owner in owners[1:]:mask[(owner-1)//8]|=1<<((owner-1)%8)
    ns.need(sum(x.bit_count()for x in mask)==1025,'official owner mask')
    return dict(Species=species,Official=owners,Representative=representatives),list(mask)

def build():
    values,mask=mappings();text=['/* pr16_dex_compact.py生成。表の意味は元namespace/version1と不変。 */','#ifndef VEGA_DEX_COMPACT_TABLES_H','#define VEGA_DEX_COMPACT_TABLES_H'];meta={}
    for name,rows in values.items():
        runs,literals=encode(rows,name!='Representative')
        text+=['static const struct VegaDexRun sCompact'+name+'[] = {']
        text+=['    {'+str(end)+'u, '+str(value)+'u},'for end,value in runs];text+=['};']
        if literals:
            text+=['static const uint16_t sCompact'+name+'Literals[] = {']
            text+=['    '+', '.join(str(v)+'u'for v in literals[i:i+16])+','for i in range(0,len(literals),16)];text+=['};']
        meta[name]=dict(keys=len(rows),records=len(runs),literal_values=len(literals),logical_bytes=4*len(runs)+2*len(literals),decoded_u16_le_sha256=hashlib.sha256(struct.pack('<'+'H'*len(rows),*rows)).hexdigest())
    text+=['const uint8_t VegaDexCompactOfficialMask[VEGA_DEX_BITMAP_SIZE] = {']
    text+=['    '+', '.join(str(v)+'u'for v in mask[i:i+16])+','for i in range(0,len(mask),16)];text+=['};','#endif','']
    source=(ROOT/ADAPTER_SOURCE).read_bytes();ns.need(hashlib.sha256(source).hexdigest()==ADAPTER_SHA256,'frozen reference adapter source')
    adapter=source.decode();replacements=[
      ('#include "dex_adapter_tables.h"','#include "dex_compact_map.h"'),
      ('_Static_assert(sizeof(sDexSpeciesOwner)/sizeof(sDexSpeciesOwner[0])==VEGA_DEX_SPECIES_SLOTS,"explicit Stage75 slot included");','_Static_assert(VEGA_DEX_SPECIES_SLOTS==1671u,"explicit Stage75 slot included");'),
      ('sid<VEGA_DEX_SPECIES_SLOTS?sDexSpeciesOwner[sid]:0u','VegaDexCompactSpeciesOwner(sid)'),
      ('national<=VEGA_DEX_OFFICIAL_COUNT?sDexOfficialOwner[national]:0u','VegaDexCompactOfficialOwner(national)'),
      ('sDexOfficialRepresentative[national]','VegaDexCompactOwnerRepresentative(VegaDexCompactOfficialOwner(national))'),
      ('sDexOfficialMask[i]','VegaDexCompactOfficialMask[i]')]
    for before,after in replacements:
        ns.need(adapter.count(before)==1,'one exact typed adapter substitution '+before);adapter=adapter.replace(before,after)
    adapter='/* pr16_dex_compact.py生成。元adapterの制御・CRC・rollbackを保ちlookupだけ置換。 */\n'+adapter
    manifest=dict(schema_version=1,status='COMPACT_MAPPING_HOST_AND_ARM_REQUIRED_ROM_UNWIRED',namespace_version=1,owner_count=1206,species_slots=1671,stage75_owner=925,reference_adapter=dict(path=ADAPTER_SOURCE,sha256=ADAPTER_SHA256),maps=meta,mask_bytes=151,reference_logical_bytes=7597,compact_logical_bytes=sum(x['logical_bytes']for x in meta.values())+151,arm_layout_padding_included=False,save_layout_changed=False,rom_wired=False)
    return {TABLE:'\n'.join(text).encode(),ADAPTER:adapter.encode(),META:(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('build','check'));args=parser.parse_args()
    for path,data in build().items():
        if args.action=='build':(ROOT/path).write_bytes(data)
        else:ns.need((ROOT/path).read_bytes()==data,'generated exact bytes '+path)
