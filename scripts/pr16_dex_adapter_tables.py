#!/usr/bin/env python3
"""stable-key namespaceからSID/公式番号の型付きconsumer表だけを生成。"""
import argparse,json
from pathlib import Path
import pr16_dex_namespace as ns
ROOT=Path(__file__).resolve().parents[1]
OUTPUT='overlays/dex_owner/dex_adapter_tables.h'
REFERENCES=('config/modernization_rockruff_own_tempo_stage75.json','content/modernization/rockruff_own_tempo_stage75_contract.json')
def extension(namespace,config=None,contract=None):
    config=json.loads((ROOT/REFERENCES[0]).read_bytes()) if config is None else config
    contract=json.loads((ROOT/REFERENCES[1]).read_bytes()) if contract is None else contract
    identity=config['identity']
    ns.need(identity==contract['identity'],'Stage75 identity source agreement')
    expected=dict(species_id=1670,normal_species_id=1142,national_dex=744,
                  species_key='SPECIES_KEY_ROCKRUFF_OWN_TEMPO',form_key='FORM_KEY_ROCKRUFF_OWN_TEMPO',
                  classification='INTERNAL_CONDITIONAL_FORM',collection_weight=0,save_layout_changed=False)
    ns.need(all(identity.get(k)==v for k,v in expected.items()),'explicit Stage75 stable-key adapter extension')
    table=contract['table_contract'];ns.need(table['old_species_count']==1670 and table['new_species_count']==1671,'Stage75 slot count')
    row=namespace['species'][1142]
    ns.need(row['species_key']=='SPECIES_KEY_ROCKRUFF' and row['owner']==namespace['official_national_to_owner'][744], 'base stable key and collection owner')
    ns.need(contract['p03']['owner_clone']['donor_species']==1142 and contract['acquisition']['target_species']==1670,'Stage75 actual form binding')
    return dict(species_id=1670,base_species_id=1142,owner=row['owner'])
def build():
    n=ns.build();extra=extension(n);owners=n['official_national_to_owner'];mask=bytearray(151)
    for owner in owners[1:]:mask[(owner-1)//8]|=1<<((owner-1)%8)
    ns.need(sum(v.bit_count()for v in mask)==1025,'unique official collection owners')
    arrays=[('uint16_t','sDexSpeciesOwner',[x['owner']for x in n['species']]+[extra['owner']]),('uint16_t','sDexOfficialOwner',owners),('uint16_t','sDexOfficialRepresentative',n['official_national_to_representative_sid']),('uint8_t','sDexOfficialMask',list(mask))]
    text=['/* pr16_dex_adapter_tables.py生成。SIDとofficialNationalは別API。 */','#ifndef VEGA_DEX_ADAPTER_TABLES_H','#define VEGA_DEX_ADAPTER_TABLES_H','#include <stdint.h>']
    for typ,name,values in arrays:
        text.append(f'static const {typ} {name}[{len(values)}] = {{')
        text.extend('    '+', '.join(str(x)+'u'for x in values[i:i+16])+','for i in range(0,len(values),16));text.append('};')
    text.extend(['#endif','']);return '\n'.join(text).encode()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('build','check'));a=p.parse_args();data=build();path=ROOT/OUTPUT
    if a.action=='build':path.write_bytes(data)
    else:ns.need(path.read_bytes()==data,'generated consumer table bytes')
