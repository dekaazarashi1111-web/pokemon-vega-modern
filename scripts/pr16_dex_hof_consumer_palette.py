"""固定DPE旧palette descriptorのpointer/tag跨ぎ一件だけを型付けする。"""
from __future__ import annotations
import csv,hashlib,io,json,re,struct
from pathlib import Path
import pr16_dex_hof_donor as d
import pr16_dex_hof_script_learnsets as legacy
import pr16_dex_hof_reference_gaps as gaps
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE=legacy.CANDIDATE
DPE=legacy.DPE
ROOT=0x09A5C4E0
COUNT=1440
SPECIES=1119
CANONICAL=1300
HIT=ROOT+SPECIES*8+2
KIND='historical_dpe_palette_pointer_tag_cross_field'
SOURCE_BLOBS={
 'config/species_surface.json':'fe52aa5d43f860a80f3b7b24681bf874ba9a8e28',
 'config/species_port.json':'4d57b01ee47286ec9c31f810db301c9df323b226',
 'state/source-lock.json':'e55a4b006cfff95995aaa703e37c401d15b86864',
 'scripts/build_species_surface.py':'6bf37ee88f559ba76997dabb8a0c35127c088342',
 'manifests/species_ids.csv':'1b3ad93740ccdcb0234c8b7f08c5b3b9d02a99d8',
 DPE+'src/Shiny_Palette_Table.c':'84594e814069145fa4c7fd3a9d8404ecc249aade',
 DPE+'include/graphics.h':'d6937044ee89e56c6ec6393c92353e5168a2e799',
 DPE+'include/species.h':'948cba1aee04dfdd9886e54d6ea8c39ad9661efb',
}
FIELDS={'schema_version','required_candidate','sources','historical_table','historical_row','historical_copy_bounds','canonical_root','canonical_row','current_actual_owner','hit','claims'}
CLAIMS=dict(historical_typing_only=True,current_runtime_reachability_claimed=False,current_reference_absence_claimed=False,retirement_completeness_claimed=False,donor_leased=False)

def sources(root,source_bytes):
 result={};texts={}
 for path,sha in SOURCE_BLOBS.items():
  raw=source_bytes[path]if path in source_bytes else(Path(root)/path).read_bytes()
  need(legacy.blob(raw)==sha,'whole independently pinned palette source '+path)
  result[path]=dict(**identity(raw),git_blob_sha=sha);texts[path]=raw.decode()
 cfg=json.loads(texts['config/species_surface.json']);sp=json.loads(texts['config/species_port.json']);lock=json.loads(texts['state/source-lock.json'])
 pins=[r for r in lock['sources']if r['name']=='dpe']
 need(len(pins)==1 and pins[0]['configured_commit']==pins[0]['resolved_commit']==sp['dpe']['commit']==legacy.DPE_COMMIT,'same original DPE build source')
 need(cfg['dpe_roots']['shiny_palette']==ROOT and cfg['counts']['dpe_species']==sp['dpe']['species_count']==COUNT and cfg['strides']['shiny_palette']==8 and cfg['pointer_sites']['shiny_palette']==0x134,'explicit original linked root, count, stride and header field')
 need(cfg['inputs']['dpe_rom_sha256']==sp['dpe']['rom_sha256']=='eb9434745801c8f82dc1eedbda3445a45bf6d5393290c1cec4e4c6697d3c820c','fixed historical DPE input identity')
 counts=legacy.constants(texts[DPE+'include/species.h'],'SPECIES_')
 need(counts['SPECIES_NICKIT']==SPECIES and counts['SPECIES_PECHARUNT']+1==COUNT and '#define NUM_SPECIES (SPECIES_PECHARUNT + 1)'in texts[DPE+'include/species.h'],'source designated selector and exact table count')
 typ=legacy.no_comments(texts[DPE+'include/graphics.h'])
 need(re.search(r'struct\s+CompressedSpritePalette\s*\{\s*const\s+u8\s*\*\s*data\s*;\s*u16\s+tag\s*;\s*u16\s+unused\s*;\s*\}\s*;',typ),'actual pointer32/tag16/unused16 C layout')
 table=legacy.no_comments(texts[DPE+'src/Shiny_Palette_Table.c'])
 need(re.search(r'const\s+struct\s+CompressedSpritePalette\s+gMonShinyPaletteTable\[NUM_SPECIES\]\s*=\s*\{',table),'one actual declared original table')
 entries=re.findall(r'\[SPECIES_NICKIT\]\s*=\s*\{\s*(\w+)\s*,\s*SPECIES_NICKIT\s*\+\s*NUM_SPECIES\s*,\s*(0x0|0)\s*\}',table)
 need(entries==[('gBackShinySprite1119NickitPal','0x0')],'exact sole designated original source initializer')
 rows=list(csv.DictReader(io.StringIO(texts['manifests/species_ids.csv'])))
 selected=[r for r in rows if r['species_key']=='SPECIES_KEY_NICKIT']
 need(len(selected)==1 and selected[0]['id']==str(CANONICAL)and selected[0]['dpe_id']==str(SPECIES)and selected[0]['dpe_symbol']=='SPECIES_NICKIT','fixed canonical mapping to original DPE selector')
 need(cfg['counts']['canonical_species']==1621 and len(rows)==1621,'original source canonical tag base, never current1671 extent')
 # Both producer functions are whole-source pinned above. Their output contract is
 # copied pointer/unused, with only the canonical resource tag rewritten.
 producer=texts['scripts/build_species_surface.py']
 need('output += slice_at(dpe, dpe_root + source * stride, stride, f"DPE {label} {source}")'in producer and 'struct.pack_into("<H", mutable, species * 8 + 4, species_count + species)'in producer,'exact bounded copy and tag-only normalization source')
 lo,hi=[d.BASE+cfg['dpe_copy'][k]for k in('start_offset','end_offset')]
 need(lo<=ROOT<ROOT+8*COUNT<=hi,'whole original table in source verbatim DPE copy')
 return result,(lo,hi)

def geometry(e):
 need(set(e)=={'historical_table','historical_row','canonical_root','canonical_row','hit','layout','source_species','canonical_species','source_symbol','claims'},'closed palette descriptor evidence')
 table,row,current,hit=e['historical_table'],e['historical_row'],e['canonical_row'],e['hit']
 need(table['address']==ROOT and table['size']==COUNT*8 and row['address']==ROOT+8*SPECIES and row['size']==8,'entire original linked table and finite row')
 need(e['layout']==dict(stride=8,pointer_offset=0,pointer_size=4,tag_offset=4,tag_size=2,unused_offset=6,unused_size=2),'complete independent field roles')
 need(e['source_species']==SPECIES and e['canonical_species']==CANONICAL and e['source_symbol']=='gBackShinySprite1119NickitPal','one source-designated descriptor')
 need(row['tag']==SPECIES+COUNT and row['unused']==0 and current['size']==8 and current['address']==e['canonical_root']['target']+CANONICAL*8 and e['canonical_root']['address']==d.BASE+0x134 and e['canonical_root']['size']==4,'actual source and canonical fields')
 need(row['pointer']==current['pointer'] and current['tag']==CANONICAL+1621 and current['unused']==0,'source producer copied pointer/unused and normalized only tag')
 need(hit['address']==HIT==row['address']+2 and hit['size']==4 and row['pointer']!=hit['target'],'crossing does not describe the real full pointer')
 need(e['claims']==CLAIMS,'historical scalar/pointer typing cannot grant runtime reachability or retirement')
 return HIT,4

def measured_regions(raw,latest,inherited,review,root,source_bytes):
 need(set(review)==FIELDS and review['schema_version']==1 and review['required_candidate']==CANDIDATE and review['claims']==CLAIMS,'closed one-row current-bound historical typing scope')
 bindings,bounds=sources(root,source_bytes)
 need(review['sources']==bindings and review['historical_copy_bounds']==list(bounds),'all source identities and original copy bounds')
 need(review['hit']==next(h for h in inherited['hits']if h['address']==HIT)and not review['hit']['accepted'],'exact inherited unknown descriptor crossing')
 gaps.bind_owner(raw,latest,review['current_actual_owner'])
 for key in('historical_table','historical_row','canonical_root','canonical_row','hit'):d.signed(raw,review[key])
 old=review['historical_row'];current=review['canonical_row'];rootrow=review['canonical_root']
 need(d.u32(raw,rootrow['address'])==rootrow['target'],'actual current header-selected canonical table')
 for row in(old,current):
  pointer,tag,unused=struct.unpack('<IHH',chunk(raw,row['address'],8))
  need((pointer,tag,unused)==(row['pointer'],row['tag'],row['unused']),'every actual row field rebinds')
  need(d.BASE<=pointer<d.BASE+len(raw)and pointer%4==0,'source data field is an aligned real pointer')
 owner=review['current_actual_owner'];need(d.contains(owner['address'],owner['address']+owner['size'],current['address'],8),'whole canonical descriptor within exact actual owner')
 e={k:review[k]for k in('historical_table','historical_row','canonical_root','canonical_row','hit','claims')}
 e.update(layout=dict(stride=8,pointer_offset=0,pointer_size=4,tag_offset=4,tag_size=2,unused_offset=6,unused_size=2),source_species=SPECIES,canonical_species=CANONICAL,source_symbol='gBackShinySprite1119NickitPal')
 start,size=geometry(e)
 return[d.TypedRegion(start,start+size,KIND,e)],dict(status='PASS_HISTORICAL_DPE_PALETTE_DESCRIPTOR_CROSSING',source_bindings=bindings,current_owner=owner['name'],claims=CLAIMS)

def regions(raw,latest,inherited,review,root,source_bytes):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'whole current0641 required before classification')
 return measured_regions(raw,latest,inherited,review,root,source_bytes)
