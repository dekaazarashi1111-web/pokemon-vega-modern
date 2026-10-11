"""受入後継表を既存consumer ABIの配置前payloadへ変換する。ROM書込はしない。

元表のcandidate_slots_zero_basedは実際にはWikiのslot+1。版固定の入力として
明示補正し、元の表・証拠は変更しない。欠落ownerを空表へ置き換えない。
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
import struct
from tools import pr16_learnset_successor as s
from tools import pr16_learnset_species_binding as b

SLOT_COUNTS = {'machine':128, 'tutor':64}
CONTRACT_PATHS = {
    'identity':'content/modernization/identity_contract.json',
    'p04_species':'content/modernization/p04_species_runtime_contract.json',
    'p04_mega':'content/modernization/p04_mega_runtime_mapping.json',
    'own_tempo':'content/modernization/rockruff_own_tempo_stage75_contract.json',
    'p02':'content/modernization/p02_evolution_contract.json',
    'caterpie':'config/modernization_p03_stage65.json',
    'p03':'content/modernization/p03_learnset_contract.json',
    'gift':'config/modernization_floette_gift.json',
}


def move_id(value):
    b.require(type(value) is int and 1 <= value <= 1062, '実装外move/bool/Side Change')
    return value


def level(row):
    b.require(row['consumer'] == 'level_up', '他consumerをlevelへ混入しない')
    source=row['provenance']['source_route']
    value=source.get('target_learning_level', source.get('learning_level', source.get('level')))
    b.require(type(value) is int and 1 <= value <= 100, 'level0/欠落/範囲外')
    return value


def pack_levels(rows):
    return b''.join(struct.pack('<HB',move_id(r['move_id']),level(r)) for r in rows)+b'\0\0\xff'


def unpack_levels(raw):
    b.require(len(raw) >= 3 and len(raw)%3 == 0 and raw[-3:] == b'\0\0\xff', 'level終端/stride不正')
    result=[]
    for at in range(0,len(raw)-3,3):
        move,lev=struct.unpack_from('<HB',raw,at)
        move_id(move); b.require(1 <= lev <= 100, 'level row不正')
        result.append((move,lev))
    return result


def pack_moves(moves):
    return b''.join(struct.pack('<H',move_id(m)) for m in moves)


def unpack_moves(raw):
    b.require(len(raw)%2 == 0, 'U16 stride不正')
    result=list(struct.unpack('<'+'H'*(len(raw)//2),raw))
    for move in result:move_id(move)
    return result


def wiki_ordinal_to_bit(ordinal, family):
    b.require(family in SLOT_COUNTS and type(ordinal) is int and 1 <= ordinal <= SLOT_COUNTS[family],
              'Wiki slotは1始まり。未知版/0/範囲外を拒否')
    return ordinal-1


def catalog(blocks, family):
    """元表で誤命名された欄の意味を固定し、同一slotの衝突を拒否する。"""
    by_bit={}
    by_move=defaultdict(set)
    for block in blocks:
        for row in block['routes']:
            b.require(row['consumer'] == family, 'catalog consumer混入')
            mid=move_id(row['move_id']); raw=row['runtime_binding']
            ordinals=raw['candidate_slots_zero_based']
            b.require(ordinals == sorted(set(ordinals)), 'slot重複/順序不正')
            expected='CANDIDATE_SLOT_REBIND_REQUIRED' if ordinals else 'ARCHIVE_ADAPTER_REQUIRED'
            b.require(raw['status'] == expected and raw['compatibility_granted'] is False
                      and raw['physical_supply_verified'] is False, '既受入catalog scope不一致')
            for ordinal in ordinals:
                bit=wiki_ordinal_to_bit(ordinal,family)
                ident=(mid,row['move_key'])
                b.require(by_bit.get(bit,ident) == ident, 'candidate slot collision')
                by_bit[bit]=ident;by_move[mid].add(bit)
    return {mid:sorted(bits) for mid,bits in by_move.items()}, by_bit


def compatibility(rows, family, by_move):
    """16byte ABI。Tutorは下位64bitのみ。旧表とのunionは行わない。"""
    b.require(family in SLOT_COUNTS, '未知compatibility family')
    bits=bytearray(16);archive=[];route_bits=[]
    for row in rows:
        b.require(row['consumer'] == family, 'compatibility consumer混入')
        mid=move_id(row['move_id']);positions=by_move.get(mid,[])
        for bit in positions:
            b.require(type(bit) is int and 0 <= bit < SLOT_COUNTS[family], 'bit範囲外')
            bits[bit//8] |= 1 << (bit%8)
        if not positions and mid not in archive:archive.append(mid)
        route_bits.append(positions)
    return bytes(bits),archive,route_bits


def bits_set(raw, family):
    b.require(len(raw)==16 and family in SLOT_COUNTS, 'compatibility stride/family不正')
    result=[n for n in range(128) if raw[n//8] & (1 << (n%8))]
    b.require(all(n < SLOT_COUNTS[family] for n in result), 'Tutor上位bit混入')
    return result


def compile_tables(root, tables, destination):
    root,tables,destination=Path(root),Path(tables),Path(destination)
    b.require(not destination.exists() and destination.is_relative_to(root/'.local')
              and '..' not in destination.parts
              and not any(p.is_symlink() for p in (destination,*destination.parents)), '新規.local出力限定')
    contracts={key:s.read_json(root/name) for key,name in CONTRACT_PATHS.items()}
    coverage=list(s.rows(tables/'species_coverage.jsonl'))
    manifest=s.manifest(root/'manifests/species_ids.csv','species_key')
    moves=s.manifest(root/'manifests/move_ids.csv','move_key')
    bindings=b.build_bindings(coverage,manifest,contracts)
    by_binding={r['species_id']:r for r in bindings}
    identities={r['species_id']:r['species_key'] for r in coverage}
    b.require(set(identities) == set(range(1671)), '現在ABIの1671 Species境界不一致')
    source_count=Counter();added_count=Counter();owner_count=Counter();policies=Counter()
    pools=defaultdict(bytearray);indexes=[];ledgers=[];added=[];catalogs={};seen=set()
    corrected=0
    for family in b.CONSUMERS:
        blocks=list(s.rows(tables/(family+'.jsonl')))
        by_species=b.unique(blocks,'species_id','species_key')
        b.require({sid:r['species_key'] for sid,r in by_species.items()}==identities, 'consumer species集合不一致')
        if family in SLOT_COUNTS:
            by_move,by_bit=catalog(blocks,family)
            catalogs[family]={'slot_count':SLOT_COUNTS[family], 'observed_slots':len(by_bit),
                              'slot_numbering':'ZERO_BASED_FOR_BINARY_ONLY',
                              'source_mislabel':'candidate_slots_zero_based actually holds Wiki one-based ordinals',
                              'slots':[dict(bit_index=bit,wiki_ordinal=bit+1,move_id=v[0],move_key=v[1])
                                       for bit,v in sorted(by_bit.items())]}
        for block in blocks:
            sid=block['species_id'];binding=by_binding.get(sid)
            donor=by_species.get(binding.get('source_species_id')) if binding else None
            base={'species_id':sid,'species_key':block['species_key'],'consumer':family}
            try:
                rows=b.query_routes(block,family,binding,donor_block=donor)
            except b.BindingRequired:
                b.require(binding and binding.get('blocking') is True, '未記録のbinding例外')
                indexes.append(dict(base,status='BLOCKED_SOURCE_ADOPTION',policy=binding['policy'],payload=None))
                continue
            if isinstance(rows,b.NonLearningIdentity):
                indexes.append(dict(base,status='IDENTITY_ONLY_NO_REPLACEMENT',identity=asdict(rows),payload=None))
                continue
            owner_count[family]+=1
            for row in rows:
                b.require(moves[row['move_id']]['move_key']==row['move_key'], 'Move ID/key不一致')
                route_key=(family,sid,row['source_id'])
                b.require(route_key not in seen, '同一owner内のsource_id重複')
                seen.add(route_key)
                if binding:
                    added.append(row);added_count[family]+=1
                else:source_count[family]+=1
            kind=family
            chunk=b'';positions=[None]*len(rows);archive=[]
            if family=='level_up':
                chunk=pack_levels(rows)
                b.require(unpack_levels(chunk)==[(r['move_id'],level(r)) for r in rows], 'level独立decode不一致')
            elif family in SLOT_COUNTS:
                chunk,archive,positions=compatibility(rows,family,by_move)
                expected=sorted({bit for row in rows for bit in by_move.get(row['move_id'],[])})
                b.require(bits_set(chunk,family)==expected, 'bit独立decode不一致')
                for row in rows:
                    if not binding:
                        raw=row['runtime_binding']['candidate_slots_zero_based']
                        expect=[wiki_ordinal_to_bit(n,family) for n in raw]
                        b.require(by_move.get(row['move_id'],[]) == expect, '元表全行slot対応不一致')
                        corrected+=bool(raw)
                name=family+'_archive';ap=pack_moves(archive);at=len(pools[name]);pools[name].extend(ap)
                b.require(unpack_moves(ap)==archive, 'archive decode不一致')
                base['archive']={'file':name+'.bin','offset':at,'size':len(ap),'moves':len(archive)}
            elif family=='egg':
                direct=[r['move_id'] for r in rows if not r['conditional_egg']]
                chunk=struct.pack('<H',20000+sid)+pack_moves(direct)
                b.require(struct.unpack_from('<H',chunk)[0]==20000+sid and unpack_moves(chunk[2:])==direct, 'egg decode不一致')
            elif family in ('evolution','reminder','shared_egg'):
                chosen=list(dict.fromkeys(r['move_id'] for r in rows));chunk=pack_moves(chosen)
                b.require(unpack_moves(chunk)==chosen, 'dedicated consumer decode不一致')
            else:
                kind='EXISTING_MOVE_SLOT_CARRY_REFERENCE' if family=='pre_evolution_carry' else 'CONDITIONAL_FORM_REFERENCE'
            offset=len(pools[family])
            if family not in ('pre_evolution_carry','form_change'):pools[family].extend(chunk)
            for row,pos in zip(rows,positions):
                policy='CONDITIONAL_BREEDING_NOT_FLAT_EGG' if family=='egg' and row['conditional_egg'] else kind
                policies[policy]+=1
                ledgers.append(dict(base,source_id=row['source_id'],route_sha256=b.identity(s.encode(row))['sha256'],
                                    policy=policy,bit_indexes_zero_based=pos, runtime_applied=False,
                                    source_table=family+'.jsonl',source_owner=row.get('binding_origin',{}).get('species_id',sid),
                                    explicit_binding=bool(binding)))
            indexes.append(dict(base,status='PAYLOAD_PREPARED_NOT_INSTALLED',routes=len(rows),
                                payload=None if family in ('pre_evolution_carry','form_change')
                                else {'file':family+'.bin','offset':offset,'size':len(chunk)}))
    pools['egg'].extend(b'\xff\xff')
    summary=dict(b.summarize(bindings),phase='SPECIES_BINDING_AND_RELOCATABLE_PAYLOADS_V1',
                 source_routes=sum(source_count.values()),source_consumers=dict(source_count),
                 explicit_binding_routes=sum(added_count.values()),binding_consumers=dict(added_count),
                 total_accounted_routes=len(ledgers),payload_owners=dict(owner_count),
                 route_policies=dict(policies),misnamed_candidate_slot_rows_corrected=corrected,
                 source_tables_modified=False,source_generations=0,native_runs=0,rom_changes=0,
                 conditional_form_runtime_connection=False,physical_supply_verified=False,
                 install_ready=False)
    destination.mkdir(parents=True)
    for name,raw in pools.items():
        if raw:(destination/(name+'.bin')).write_bytes(raw)
    for name,rows in [('species-bindings.jsonl',bindings),('consumer-index.jsonl',indexes),
                      ('route-ledger.jsonl',ledgers),('binding-routes.jsonl',added)]:
        (destination/name).write_bytes(b''.join(s.encode(r) for r in rows))
    (destination/'catalogs.json').write_bytes(s.encode(catalogs))
    summary['inputs']={name:s.identity(root/name) for name in list(CONTRACT_PATHS.values())+
                       ['manifests/species_ids.csv','manifests/move_ids.csv','scripts/pr16_candidate_wiki_extract.py']}
    summary['files']={p.name:s.identity(p) for p in sorted(destination.iterdir())}
    (destination/'receipt.json').write_bytes(s.encode(summary))
    return summary


def require_install_ready(report):
    b.require(report.get('install_ready') is True and not report.get('blocking')
              and report.get('conditional_form_runtime_connection') is True
              and report.get('physical_supply_verified') is True, '未解決owner/条件/供給。ROMへの一括適用は禁止')
