#!/usr/bin/env python3
"""stable-key namespaceからSID/公式番号の型付きconsumer表だけを生成。"""
import argparse
from pathlib import Path
import pr16_dex_namespace as ns
ROOT=Path(__file__).resolve().parents[1]
OUTPUT='overlays/dex_owner/dex_adapter_tables.h'
def build():
    n=ns.build();owners=n['official_national_to_owner'];mask=bytearray(151)
    for owner in owners[1:]:mask[(owner-1)//8]|=1<<((owner-1)%8)
    ns.need(sum(v.bit_count()for v in mask)==1025,'unique official collection owners')
    arrays=[('uint16_t','sDexSpeciesOwner',[x['owner']for x in n['species']]),('uint16_t','sDexOfficialOwner',owners),('uint16_t','sDexOfficialRepresentative',n['official_national_to_representative_sid']),('uint8_t','sDexOfficialMask',list(mask))]
    text=['/* pr16_dex_adapter_tables.py生成。SIDとofficialNationalは別API。 */','#ifndef VEGA_DEX_ADAPTER_TABLES_H','#define VEGA_DEX_ADAPTER_TABLES_H','#include <stdint.h>']
    for typ,name,values in arrays:
        text.append(f'static const {typ} {name}[{len(values)}] = {{')
        text.extend('    '+', '.join(str(x)+'u'for x in values[i:i+16])+','for i in range(0,len(values),16));text.append('};')
    text.extend(['#endif','']);return '\n'.join(text).encode()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('build','check'));a=p.parse_args();data=build();path=ROOT/OUTPUT
    if a.action=='build':path.write_bytes(data)
    else:ns.need(path.read_bytes()==data,'generated consumer table bytes')
