"""固定DPEの実initializerと歴史pointer根から、隣接数値列の9境界だけを検証する。"""
from __future__ import annotations
import hashlib
import json
import re
import struct
from pathlib import Path

import pr16_dex_hof_donor as d

need, identity, chunk = d.need, d.identity, d.chunk
CANDIDATE = dict(size=33554432, sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
DPE_COMMIT = '10ff98c85ebf37ab5cb39a41b6e9b50f06efb19e'
DPE = 'vendor/upstream/DPE-JP/'
ROOT_ADDRESS = 0x09A410F4
ROOT_COUNT = 1440
# (hit, left species, right species)。現1671species表とは別の固定DPE namespace。
PAIRS = ((0x09A436E9,1344,1343), (0x09A44B5C,1182,1181),
         (0x09A45957,1102,1084), (0x09A46C6B,954,953),
         (0x09A48B1F,654,653), (0x09A48B58,653,652),
         (0x09A4A676,521,520), (0x09A4DF64,182,181),
         (0x09A4EA3E,128,127))
SOURCE_BLOBS = {
    'scripts/build_species_surface.py':'6bf37ee88f559ba76997dabb8a0c35127c088342',
    'config/species_surface.json':'fe52aa5d43f860a80f3b7b24681bf874ba9a8e28',
    'config/species_port.json':'4d57b01ee47286ec9c31f810db301c9df323b226',
    'state/source-lock.json':'e55a4b006cfff95995aaa703e37c401d15b86864',
    DPE+'src/Learnsets.c':'3902ece10bcba93dfc4ec8329d2820f203e3265c',
    DPE+'src/defines.h':'776b61443c25ce9fec55e4c8c5fa141a438c68f1',
    DPE+'include/species.h':'948cba1aee04dfdd9886e54d6ea8c39ad9661efb',
    DPE+'include/moves.h':'a85baa685a8d9d1e257f8c2514330802e92581d5',
}


def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def source_proof(root, sources=None):
    """上流を含む実source全byteを固定。dictはcanonical repository path→bytes。"""
    sources = sources or {}
    bound, texts = {}, {}
    for path, expected in SOURCE_BLOBS.items():
        if path in sources:
            raw = sources[path]
            need(type(raw) is bytes, 'source dictionary contains exact bytes')
        else:
            file = Path(root)/path
            need(file.is_file() and not file.is_symlink(), 'regular fixed source '+path)
            raw = file.read_bytes()
        need(blob(raw) == expected, 'whole pinned source Git blob '+path)
        bound[path] = dict(**identity(raw), git_blob_sha=expected)
        texts[path] = raw.decode('utf-8')
    config = json.loads(texts['config/species_surface.json'])
    species = json.loads(texts['config/species_port.json'])
    lock = json.loads(texts['state/source-lock.json'])
    upstream = [x for x in lock['sources'] if x['name']=='dpe']
    need(len(upstream)==1 and upstream[0]['configured_commit']==DPE_COMMIT and
         upstream[0]['resolved_commit']==DPE_COMMIT, 'same fixed DPE source pin')
    need(config['dpe_roots']['level_up']==ROOT_ADDRESS and
         config['counts']['dpe_species']==ROOT_COUNT==species['dpe']['species_count'] and
         species['dpe']['commit']==DPE_COMMIT and
         config['inputs']['dpe_rom_sha256']==species['dpe']['rom_sha256'],
         'historical linked root and original input identity, not current runtime root')
    lo, hi = (config['dpe_copy'][x]+d.BASE for x in ('start_offset','end_offset'))
    need(lo<=ROOT_ADDRESS<ROOT_ADDRESS+ROOT_COUNT*4<=hi, 'fixed verbatim DPE copy contains root')
    need('#define EXPAND_LEARNSETS' in texts[DPE+'src/defines.h'], 'actual expanded input ABI')
    return texts, bound, (lo,hi)


def no_comments(text):
    return re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)


def constants(text, prefix):
    pairs = re.findall(r'^\s*#define\s+('+re.escape(prefix)+r'\w+)\s+(0[xX][0-9A-Fa-f]+|\d+)\s*$', no_comments(text), re.M)
    result = {}
    for name, value in pairs:
        need(name not in result, 'unique scalar source constant')
        result[name] = int(value,0)
    return result


def parse_array(body, moves):
    """公開C initializerの小文法。raw ROM bytesも任意C実行も不要。"""
    body = no_comments(body).strip()
    token = re.compile(r'\s*(?:LEVEL_UP_MOVE\(\s*(\d+)\s*,\s*(MOVE_\w+)\s*\)|(?P<end>LEVEL_UP_END))\s*(,|$)')
    at, data, ended, count = 0, bytearray(), False, 0
    while at < len(body):
        m=token.match(body,at)
        need(m is not None and not ended, 'complete source initializer tokens and one final sentinel')
        at=m.end()
        if m.group('end'):
            data += struct.pack('<HB',0,255)
            ended=True
        else:
            level, symbol=int(m.group(1)),m.group(2)
            need(symbol in moves and 0<moves[symbol]<=65535 and 0<=level<=100,
                 'u16 move/u8 level numeric source domain')
            data += struct.pack('<HB',moves[symbol],level)
            count+=1
    need(ended and count<=255, 'bounded complete source numeric sequence')
    return bytes(data), count


def source_model(texts):
    source=texts[DPE+'src/Learnsets.c']
    clean=no_comments(source)
    need(re.search(r'struct\s+__attribute__\(\(packed\)\)\s+LevelUpMove\s*\{\s*u16\s+move;\s*u8\s+level;\s*\};',clean)
         is not None and '#define LEVEL_UP_MOVE(lvl, move) {move, lvl}' in clean and
         '#define LEVEL_UP_END {0x0, 0xFF}' in clean, 'actual packed scalar source ABI and terminator')
    species=constants(texts[DPE+'include/species.h'],'SPECIES_')
    moves=constants(texts[DPE+'include/moves.h'],'MOVE_')
    need(species['SPECIES_PECHARUNT']+1==ROOT_COUNT and
         '#define NUM_SPECIES (SPECIES_PECHARUNT + 1)' in texts[DPE+'include/species.h'],
         'fixed declared root-table length')
    table=re.findall(r'const\s+struct\s+LevelUpMove\*\s+const\s+gLevelUpLearnsets\[NUM_SPECIES\]\s*=\s*\{(.*?)\};',clean,re.S)
    need(len(table)==1, 'one exact designated source root table')
    entries={}
    token=re.compile(r'\s*\[(SPECIES_\w+|\d+)\]\s*=\s*(\w+)\s*,')
    body=table[0].strip(); at=0
    while at<len(body):
        m=token.match(body,at);need(m is not None,'complete designated source root grammar')
        sp,name=m.groups();need(sp in species or sp.isdecimal(),'defined source species')
        sid=int(sp) if sp.isdecimal() else species[sp]
        need(sid not in entries and 0<=sid<ROOT_COUNT,'unique bounded source root selector')
        entries[sid]=(sp,name);at=m.end()
    need(set(entries)==set(range(ROOT_COUNT)),'complete source root table, no implied holes')
    arrays={}
    selected={sid for _,left,right in PAIRS for sid in (left,right)}
    for sid in sorted(selected):
        sp,name=entries[sid]
        matches=list(re.finditer(r'static\s+const\s+struct\s+LevelUpMove\s+'+re.escape(name)+r'\[\]\s*=\s*\{(.*?)\};',clean,re.S))
        need(len(matches)==1,'one exact public initializer for selected source root')
        m=matches[0];data,count=parse_array(m.group(1),moves)
        original=re.search(r'static\s+const\s+struct\s+LevelUpMove\s+'+re.escape(name)+r'\[\]',source)
        arrays[sid]=dict(species_symbol=sp,array_symbol=name,payload=data,row_count=count,
                         source_line=source.count('\n',0,original.start())+1)
    return arrays


def _regions(raw, review, root, sources=None):
    """診断専用入口。親Actionsは必ずregions()の現候補全SHA gateを通す。"""
    texts, bindings, (lo,hi)=source_proof(root,sources)
    need(review['required_candidate']==CANDIDATE and review['schema_version']==1,
         'explicit required current identity')
    need(review['sources']==bindings,'all declared source identities match pinned actual source')
    arrays=source_model(texts)
    table=review['historical_root_table']
    need((table['address'],table['size'],table['count'])==(ROOT_ADDRESS,ROOT_COUNT*4,ROOT_COUNT),
         'original concrete linked root table, never modern species pointer array')
    d.signed(raw,table)
    need(set(review['sequences'])==set(map(str,arrays)),'exact finite initializer-root set')
    sequences={}
    roles=[dict(address=ROOT_ADDRESS,size=ROOT_COUNT*4,role='historical_dpe_species_pointer_table')]
    for sid,model in arrays.items():
        row=review['sequences'][str(sid)]
        pointer=row['pointer'];span=row['span']
        d.signed(raw,pointer);d.signed(raw,span)
        address=ROOT_ADDRESS+sid*4
        need(pointer['address']==address and pointer['size']==4 and
             d.u32(raw,address)==pointer['target']==span['address'], 'actual exact species-indexed historical pointer')
        need(span['size']==len(model['payload']) and
             ROOT_ADDRESS+ROOT_COUNT*4<=span['address'] and span['address']+span['size']<=hi,
             'whole bounded source sequence outside pointer role')
        need(chunk(raw,span['address'],span['size'])==model['payload'],
             'every numeric byte equals actual public source initializer')
        need(row['row_count']==model['row_count'] and row['array_symbol']==model['array_symbol'] and
             row['species_symbol']==model['species_symbol'] and row['source_line']==model['source_line'],
             'source selector, array symbol and scalar extent binding')
        sequences[sid]=dict(species_id=sid,**row)
        roles.append(dict(address=span['address'],size=span['size'],role='historical_dpe_packed_numeric_sequence'))
    ordered=sorted((r['span']['address'],r['span']['address']+r['span']['size']) for r in sequences.values())
    need(all(a[1]<=b[0] for a,b in zip(ordered,ordered[1:])), 'distinct selected numeric sequences never overlap')
    need(len(review['boundaries'])==len(PAIRS),'exact nine reviewed boundaries')
    regions,witnesses=[],[]
    for expected,row in zip(PAIRS,review['boundaries']):
        hit=row['hit']; address,left,right=expected
        need((hit['address'],row['left_species_id'],row['right_species_id'])==expected and
             hit['size']==4 and hit['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS' and
             hit['classification']=='UNCLASSIFIED' and hit['accepted'] is False and
             hit['owner_candidates']==[], 'exact prior unowned unknown identity and selectors')
        d.signed(raw,hit)
        a,b=sequences[left]['span'],sequences[right]['span'];boundary=b['address']
        need(a['address']+a['size']==boundary and address==boundary-3,
             'both actual roots meet: whole terminal triple then first byte of next scalar')
        need(chunk(raw,boundary-3,3)==struct.pack('<HB',0,255) and
             len(arrays[right]['payload'])>=6,'actual source sentinel followed by nonempty numeric sequence')
        window=dict(address=boundary-3,**identity(chunk(raw,boundary-3,6)))
        need(row['typed_window']==window,'exact six-byte numeric boundary, no pointers or padding')
        witness=dict(hit=hit,typed_window=window,left=sequences[left],right=sequences[right],
                     source_root=DPE+'src/Learnsets.c#gLevelUpLearnsets',
                     scalar_abi='PACKED_LE_U16_MOVE_U8_LEVEL; terminal MOVE0_LEVEL255',
                     historical_typing_only=True,current_runtime_reachability_claimed=False,
                     current_reference_absence_claimed=False,retirement_completeness_claimed=False)
        regions.append(d.TypedRegion(window['address'],window['address']+window['size'],
                                     'legacy_dpe_level_numeric_boundary',witness))
        witnesses.append(witness)
    return regions,dict(status='PASS_FINITE_HISTORICAL_DPE_INITIALIZER_BOUNDARIES',count=len(regions),
        historical_root_table=table,witnesses=witnesses,source_bindings=bindings,root_role_windows=roles,
        historical_typing_only=True,current_runtime_reachability_claimed=False,
        current_reference_absence_claimed=False,retirement_completeness_claimed=False,
        donor_leased=False,donor_eligible=False,indirect_reference_completeness_claimed=False,
        whole_rom_scan_runs=0,rom_writes=0,native_processes=0)


def regions(raw, review, root, sources=None):
    need(identity(raw)==CANDIDATE,'current whole candidate mandatory before historical typing')
    return _regions(raw,review,root,sources)
