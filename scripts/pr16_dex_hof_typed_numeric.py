#!/usr/bin/env python3
"""旧習得表を固定serializer/receipt/C ABI/現byte ownerで束縛する読取専用分類。"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

import pr16_dex_hof_donor as donor

ROOT = Path(__file__).resolve().parents[1]
need, identity = donor.need, donor.identity
CANDIDATE = dict(size=33554432, sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
RECEIPT = 'content/modernization/pr16_learnset_natural_checkpoint.json'
REVIEW = 'content/modernization/pr16_dex_hof_typed_numeric_review.json'
RECEIPT_ID = dict(size=93858, sha256='f15336e39b840f21bcd7ef30a0b1989421a0516ffd80a7a527266186e69fdf69')
# Git管理外upstreamもstate/source-lock固定commit e24a16feの全byteを検証する。
SOURCE_GIT_BLOB = {
    'scripts/build_species_surface.py': '6bf37ee88f559ba76997dabb8a0c35127c088342',
    'config/species_surface.json': 'fe52aa5d43f860a80f3b7b24681bf874ba9a8e28',
    'overlays/species_surface/species_runtime.c': '9dea3285b66b807775d188b84eb8b7a5a42130cd',
    'tools/modernization_p03_stage66.py': '68df88ebbc8d8736f77e15b57ae250e756aa0a8a',
    'tools/modernization_p03_stage67.py': '109774489421e6740bc42946fc8213443d703960',
    'config/modernization_p03_stage66.json': '298249025df1f55741724a8eef7361b53d96a4f3',
    'config/modernization_p03_stage67.json': 'e9324d793c98ae89057b6cede188b01218ad85d7',
    'content/modernization/p03_stage66_checkpoint.json': '8149545df2b7fa07ee0c216ee1fa4c451c73c82a',
    'content/modernization/p03_stage67_checkpoint.json': 'f94f9c4164b860bc68124a181b54eaa21f2a97c1',
    'scripts/pr16_p07_preserved_layer.py': 'd69235a4b023aa17aaaee61709ec3e08a6b2ff8c',
    'vendor/upstream/CFRU-JP/src/learn_move.c': 'a450dfbdc07289ce1f1c57018f9fccb130fe2db0',
    'vendor/upstream/CFRU-JP/include/pokemon.h': 'b18f2ee2a1517efa8aeb742daedac9e778d73d7a',
    'vendor/upstream/CFRU-JP/src/item.c': 'ea5302c0dc2bb9fc92e665aab6015a27ff4275d7',
    'vendor/upstream/CFRU-JP/src/config.h': 'd8b75dcb495c22b4b81d69d2b3c093de6d788c7d',
    'config/cfru_vega_minimal.h': 'dacccff5804eafd687773c77b880a9108ae45f3f',
    'scripts/build_move_distribution_v4.py': '34c63db8909b1c3d7e302ba2ea50a8c53fca0f12',
    'config/move_distribution_v4.json': '21c9e42f655ff1c910778211f5e8a347ae0ed52d',
    'overlays/move_distribution_v4/move_distribution_v4.c': '10ba2ee9cfd32089ee4afa2fdc9bb9e0445475e1',
    'overlays/move_distribution_v4/move_distribution_v4.h': '8e2360f7c4be34eaa904af12c6ef8837420fa732',
    'content/modernization/p04_capacity_allocation_manifest.json': '1c765294889d44df4d9f9375c88b814e31a653db',
}
T09 = 'species_surface_level_up_data'
S66 = 'modernization_p03_stage66_bulk_level_up'
S67 = 'modernization_p03_stage67_evolution_level_rows'
P07 = 'modernization-p07-preserved-level'
S39 = 'move_distribution_v4_stage39_payload'
S39_LAYOUT = dict(address=154739872, size=177104,
                  sha256='da99b4b2a074038aefb57bdd18b82e29b839383f7e73278fe95e5843c52598b2')
S39_HISTORICAL_SHA = 'd2b11236d8c586986c44329c6772337e1cc0e32ed782a615f61a52b208a21227'
S39_METADATA = 'build/stages/39_move_distribution_v4.json'
S39_METADATA_ID = dict(size=11583, sha256='c39a7903d1801c791fae6f983f766a8a4a009e6d3c360bfa3ca533290b9527b3')
S39_ORIGINAL_TABLES = dict(pointers=154815660, tutor=154868520, form=154894456)
S39_ZERO_ROWS = 15
LAYOUTS = {
    T09: dict(address=167430584, size=81885, sha256='4544753386775f0330073d879222e4bf9527a49183c3a06d83559a32d73440c3',
              sequences=1621, alignment=1, max_rows=255, prefix=0, zero_move_zero_level_rows=14,
              serializer='scripts/build_species_surface.py#merge_learnsets'),
    S66: dict(address=167617096, size=60116, sha256='0bde103cdbc375ec7842a72b79ba9cd85a9ea54e2d489848f5e098696281a09b',
              sequences=1300, alignment=2, max_rows=255, prefix=0,
              serializer='tools/modernization_p03_stage66.py#_serialize_level_payload'),
    S67: dict(address=167677212, size=17319, sha256='bc2546ffb6cc68c0e678da572a24df1ac0be7793a60d92d6673719c4e41e11ee',
              sequences=330, alignment=2, max_rows=50, prefix=0,
              serializer='tools/modernization_p03_stage67.py#_serialize_evolution_payload'),
    P07: dict(address=157114352, size=16137, sha256='a53aa7ced55de4a1333245678ee3060b230cea898b8246483960659bac19dd12',
              sequences=None, alignment=1, max_rows=40, prefix=1671 * 4,
              serializer='scripts/pr16_p07_preserved_layer.py#level_bytes'),
}


def fixed_file(root, path):
    file = root / path
    need(file.is_file() and not file.is_symlink(), 'regular fixed numeric source: ' + path)
    return file.read_bytes()


def source_proof(root=ROOT):
    """名前やmanifestだけの追認を防ぎ、元の型定義・生成境界を固定する。"""
    documents, bindings = {}, {}
    for path, expected in SOURCE_GIT_BLOB.items():
        raw = fixed_file(root, path)
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        need(blob == expected, 'fixed numeric source Git blob drift: ' + path)
        bindings[path] = dict(**identity(raw), git_blob_sha=blob)
        if path.endswith('.json'):
            documents[path] = json.loads(raw)
    raw = fixed_file(root, RECEIPT)
    need(identity(raw) == RECEIPT_ID, 'fixed historical numeric output receipt')
    bindings[RECEIPT] = identity(raw)
    receipt = json.loads(raw)
    allocations = receipt['wild_repair']['allocation']['allocations']
    for name, layout in LAYOUTS.items():
        rows = [r for r in allocations if r['name'] == name]
        need(len(rows) == 1, 'one original numeric allocation receipt')
        row = rows[0]
        need((row['gba_start'], row['size'], row['content_sha256']) ==
             (layout['address'], layout['size'], layout['sha256']), 'historical numeric output identity')
    surface = documents['config/species_surface.json']
    need(surface['counts']['canonical_species'] == 1621 and
         surface['counts']['tutor_bytes_per_species'] == 16, 'original T09 species/stride receipt')
    for stage, owner in ((66, S66), (67, S67)):
        config = documents[f'config/modernization_p03_stage{stage}.json']
        declared = config['allocation'] if stage == 66 else config['allocations'][0]
        layout = LAYOUTS[owner]
        need((declared['name'], int(declared['start'], 16) + donor.BASE, declared['size'],
              declared['content_sha256'], declared['row_start_alignment']) ==
             (owner, layout['address'], layout['size'], layout['sha256'], layout['alignment']),
             'fixed stage serializer output and alignment contract')
        cp = documents[f'content/modernization/p03_stage{stage}_checkpoint.json']
        need(cp['acceptance']['static_contract_gate'] == 'PASS' and
             cp['acceptance']['real_consumer_mgba_gate'] == 'PASS', 'historical numeric consumer receipt')
    original39 = [r for r in allocations if r['name'] == S39]
    need(len(original39) == 1 and
         (original39[0]['gba_start'], original39[0]['size'], original39[0]['content_sha256']) ==
         (S39_LAYOUT['address'], S39_LAYOUT['size'], S39_HISTORICAL_SHA),
         'fixed Stage39 historical extent; nominal hash is not current authority')
    config39 = documents['config/move_distribution_v4.json']
    need(config39['counts'] == dict(species=1621, moves=1063, level_up_rows=28274,
         egg_rows=8219, tm_tutor_changes=2799, form_rows=509, wild_rows=1206,
         source_rows=1206, tm_slots=120, tutor_slots=64, compatibility_stride=16),
         'fixed Stage39 serialized domain counters')
    capacity = documents['content/modernization/p04_capacity_allocation_manifest.json']
    for key, table, size in (('species_level_up_pointers', 'pointers', 1621*4),
                             ('species_tutor', 'tutor', 1621*16),
                             ('form_resolution', 'form', 509*14)):
        rows = [r for r in capacity['table_capacity']['fixed_tables'] if r['table_key'] == key]
        need(len(rows) == 1 and (rows[0]['current_address'], rows[0]['old_size_bytes']) ==
             (S39_ORIGINAL_TABLES[table], size), 'independent original Stage39 table geometry receipt')
    original_meta = capacity['inputs']['stage39_move_distribution_metadata']
    need({k: original_meta[k] for k in ('size', 'sha256')} == S39_METADATA_ID,
         'independent original Stage39 metadata identity receipt')
    return bindings


def parse_sequences(payload, address, count, alignment, max_rows, zero_move_zero_level_rows=0):
    """既知serializerの先頭から全列を一度だけ解読。FF整列byteは型領域に入れない。"""
    need(type(count) is int and count > 0 and type(alignment) is int and alignment in (1, 2) and
         type(max_rows) is int and 0 <= max_rows <= 255 and
         type(zero_move_zero_level_rows) is int and zero_move_zero_level_rows >= 0,
         'explicit numeric sequence bounds')
    cursor, spans, padding, zero_rows = 0, [], [], 0
    for ordinal in range(count):
        if cursor % alignment:
            need(cursor < len(payload) and payload[cursor] == 255, 'exact excluded FF alignment byte')
            padding.append(dict(address=address + cursor, size=1))
            cursor += 1
        start, span_zero_rows = cursor, 0
        for rows in range(max_rows + 1):
            need(cursor + 3 <= len(payload), 'bounded complete numeric sequence')
            move, level = struct.unpack_from('<HB', payload, cursor)
            cursor += 3
            if (move, level) == (0, 255):
                break
            if (move, level) == (0, 0) and zero_move_zero_level_rows:
                zero_rows += 1
                span_zero_rows += 1
            else:
                need(1 <= move <= 1062 and 0 <= level <= 100, 'LE_U16 move/U8 level scalar ABI')
        else:
            raise ValueError('numeric sequence exceeds fixed consumer bound')
        spans.append(dict(ordinal=ordinal, address=address + start, row_count=rows,
                          zero_move_zero_level_rows=span_zero_rows,
                          **identity(payload[start:cursor])))
    need(cursor == len(payload), 'complete numeric payload coverage without trailing bytes')
    need(zero_rows == zero_move_zero_level_rows, 'exact fixed MOVE0_LEVEL0 row count')
    return spans, padding


def decode_level_pool(payload, owner, layout):
    """全ownerのactual afterSHA照合後、型領域と非型pointer/paddingを分離する。"""
    observed = identity(payload)
    need((owner['address'], owner['size'], owner['after_sha256']) ==
         (layout['address'], observed['size'], observed['sha256']) and
         observed == {key: layout[key] for key in ('size', 'sha256')},
         'latest actual numeric byte-owner and immutable source output')
    prefix = layout['prefix']
    need(type(prefix) is int and 0 <= prefix < len(payload) and prefix % 4 == 0,
         'bounded pointer prefix')
    pointer_entries = []
    if prefix:
        lo, hi = owner['address'], owner['address'] + len(payload)
        for sid, (target,) in enumerate(struct.iter_unpack('<I', payload[:prefix])):
            need(donor.BASE <= target < donor.BASE + 33554432, 'bounded historical level pointer')
            need(not lo <= target < lo + prefix, 'pointer prefix cannot be numeric payload')
            if lo + prefix <= target < hi:
                pointer_entries.append(dict(species_id=sid, target=target))
        need(pointer_entries and [r['target'] for r in pointer_entries] ==
             sorted(set(r['target'] for r in pointer_entries)), 'unique serializer-ordered P07 pointers')
        count = len(pointer_entries)
    else:
        count = layout['sequences']
    spans, padding = parse_sequences(payload[prefix:], owner['address'] + prefix, count,
                                     layout['alignment'], layout['max_rows'],
                                     layout.get('zero_move_zero_level_rows', 0))
    if prefix:
        need([r['address'] for r in spans] == [r['target'] for r in pointer_entries],
             'every P07 pointer resolves exact emitted sequence start')
        for span, pointer in zip(spans, pointer_entries):
            span['species_id'] = pointer['species_id']
    evidence = dict(owner=owner['name'], actual_owner=dict(address=owner['address'], **observed),
                    owner_after_sha256=owner['after_sha256'], source_receipt=RECEIPT,
                    serializer=layout['serializer'],
                    consumer_abi='vendor/upstream/CFRU-JP/include/pokemon.h#LevelUpMove',
                    consumer='vendor/upstream/CFRU-JP/src/learn_move.c#GetLevelUpMovesBySpecies',
                    numeric_encoding='LE_U16_MOVE_U8_LEVEL; terminal MOVE0_LEVEL255',
                    historical_typing_only=True, current_consumer_reachability_claimed=False)
    regions = []
    for span in spans:
        regions.append(donor.TypedRegion(span['address'], span['address'] + span['size'],
                       'legacy_level_numeric', dict(evidence, row_spans=[span])))
    # 同じserializerの隣接列だけを橋渡しする。pointer prefix/padding/別ownerを結合しない。
    for left, right in zip(spans, spans[1:]):
        end = left['address'] + left['size']
        if end == right['address']:
            regions.append(donor.TypedRegion(end - 3, end + 3, 'legacy_level_numeric',
                           dict(evidence, row_spans=[left, right], exact_numeric_boundary=end)))
    summary = dict(owner=owner['name'], address=owner['address'], **observed,
                   sequence_count=len(spans), numeric_rows=sum(r['row_count'] for r in spans),
                   typed_bytes=sum(r['size'] for r in spans), excluded_alignment_bytes=len(padding),
                   zero_move_zero_level_rows=sum(r['zero_move_zero_level_rows'] for r in spans),
                   excluded_pointer_bytes=prefix, padding=padding,
                   complete_partition=sum(r['size'] for r in spans) + len(padding) + prefix == len(payload))
    need(summary['complete_partition'], 'complete pointer/numeric/padding partition')
    if prefix:
        summary['pointer_prefix'] = dict(address=owner['address'], **identity(payload[:prefix]))
    return regions, summary


def unindexed_level_sequences(payload, address):
    """退役・repoint済みpointerを根拠にせず、固定serializerの全数値列と末尾FFを区分。"""
    tails = [tail for tail in range(4) if len(payload) > tail and
             (len(payload) - tail) % 3 == 0 and
             (tail == 0 or payload[-tail:] == b'\xff' * tail) and
             payload[len(payload)-tail-3:len(payload)-tail] == b'\0\0\xff']
    need(len(tails) == 1, 'unique Stage39 numeric terminal and excluded tail alignment')
    tail = tails[0]
    data = payload[:len(payload)-tail]
    count = sum(row == (0, 255) for row in struct.iter_unpack('<HB', data))
    need(0 < count <= 1621, 'bounded Stage39 serialized source sequences')
    spans, padding = parse_sequences(data, address, count, 1, 255, S39_ZERO_ROWS)
    need(not padding and sum(r['row_count'] for r in spans) <= 28274,
         'Stage39 selected source rows remain within fixed input domain')
    return spans, tail


def stage39_regions(payload, owner, metadata=None):
    observed = identity(payload)
    need(owner['name'] == S39 and
         (owner['address'], owner['size'], owner['after_sha256']) ==
         (S39_LAYOUT['address'], observed['size'], observed['sha256']) and
         observed == {k: S39_LAYOUT[k] for k in ('size', 'sha256')},
         'latest whole Stage39 actual owner identity')
    need(len(payload) >= 256, 'whole Stage39 header')
    values = struct.unpack_from('<8s16I', payload)
    (magic, version, total, header, code_size, pointers, egg, tmhm, tutor,
     form, wild, level_rows, egg_rows, changes, forms, wild_rows, sources) = values
    need((magic, version, total, header, level_rows, egg_rows, changes, forms, wild_rows, sources) ==
         (b'VEGAMD39', 1, len(payload), 256, 28274, 8219, 2799, 509, 1206, 1206),
         'fixed Stage39 serializer header and counter ABI')
    base = owner['address']
    align = lambda value, size=4: (value + size - 1) & -size
    start = align(header + code_size)
    # downstreamはheader内のlevel/tutor/wild rootもrepointする。固定P04受入receiptの
    # 元の物理table境界を使い、現rootを退役poolへ読み替えない。
    original_pointers = S39_ORIGINAL_TABLES['pointers']
    original_tutor = S39_ORIGINAL_TABLES['tutor']
    pointer_at = original_pointers - base
    need(0 < code_size <= 32768 and 256 < start < pointer_at < len(payload) and
         all(value % 4 == 0 for value in (pointers, egg, tmhm, tutor, form, wild)) and
         all(donor.BASE <= value < donor.BASE + 33554432 for value in (pointers, tutor, wild)) and
         original_pointers + 1621 * 4 == egg < tmhm and
         tmhm + 1621 * 16 == original_tutor and original_tutor + 1621 * 16 == form and
         form == S39_ORIGINAL_TABLES['form'] and
         align(align(form + forms * 14) + 1621 * 8 + sources * 2, 16) == base + len(payload),
         'bounded disjoint Stage39 code/numeric/pointer/other-table geometry')
    need(payload[72:256] == b'\xff' * 184 and
         payload[header+code_size:start] == b'\xff' * (start-header-code_size),
         'excluded Stage39 header/code alignment bytes')
    spans, tail = unindexed_level_sequences(payload[start:pointer_at], base + start)
    stop = pointer_at - tail
    pool = dict(address=base + start, **identity(payload[start:stop]))
    code = dict(address=base + header, **identity(payload[header:header+code_size]))
    if metadata is not None:
        # metadataは呼出側で固定whole-file identity照合済み。古いpointer/content hashで
        # 現ownerを追認せず、対象の数値poolだけを独立照合する。
        old = metadata['runtime']
        need(old['tables']['level_up_data'] == pool,
             'original Stage39 metadata numeric pool identity')
        need(old['payload']['address'] == base and old['payload']['size'] == len(payload) and
             old['payload']['sha256'] == S39_HISTORICAL_SHA and
             old['code']['address'] == code['address'] and old['code']['size'] == code['size'],
             'original Stage39 metadata owner/code geometry')
    evidence = dict(owner=S39, actual_owner=dict(address=base, **observed),
                    owner_after_sha256=owner['after_sha256'],
                    historical_allocation_sha256=S39_HISTORICAL_SHA,
                    historical_nominal_hash_used_as_current=False, source_receipt=RECEIPT,
                    serializer='scripts/build_move_distribution_v4.py#_table_blobs',
                    consumer='overlays/move_distribution_v4/move_distribution_v4.c#MoveDistributionV4_GiveInitialMoves',
                    numeric_encoding='LE_U16_MOVE_U8_LEVEL; terminal MOVE0_LEVEL255',
                    header=dict(address=base, **identity(payload[:256])), pool=pool,
                    current_consumer_reachability_claimed=False,
                    current_repointed_species_pointers_used_as_historical_roots=False,
                    relocated_header_roots_not_old_pool_authority=True,
                    original_boundary_receipt='content/modernization/p04_capacity_allocation_manifest.json',
                    metadata_verified=metadata is not None)
    regions = [donor.TypedRegion(r['address'], r['address'] + r['size'],
               'legacy_level_numeric', dict(evidence, row_spans=[r])) for r in spans]
    for left, right in zip(spans, spans[1:]):
        end = left['address'] + left['size']
        need(end == right['address'], 'complete contiguous Stage39 numeric coverage')
        regions.append(donor.TypedRegion(end - 3, end + 3, 'legacy_level_numeric',
                       dict(evidence, row_spans=[left, right], exact_numeric_boundary=end)))
    summary = dict(owner=S39, address=base, **observed, pool=pool, excluded_code=code,
                   sequence_count=len(spans), numeric_rows=sum(r['row_count'] for r in spans),
                   zero_move_zero_level_rows=sum(r['zero_move_zero_level_rows'] for r in spans),
                   typed_bytes=stop-start, excluded_alignment_bytes=tail,
                   excluded_pointer_bytes=1621*4,
                   excluded_total_bytes=len(payload)-(stop-start),
                   complete_partition=(stop-start)+start+tail+(len(payload)-pointer_at)==len(payload),
                   metadata_verified=metadata is not None,
                   proof_mode='FIXED_METADATA_POOL_AND_CURRENT_OWNER' if metadata is not None else
                              'FIXED_SERIALIZER_HEADER_C_ABI_AND_CURRENT_OWNER')
    return regions, summary


def numeric_regions(raw, latest, root=ROOT):
    """主Actionsの一度の現候補再構成を受け取る。全ROM再走査・native・再生成は行わない。"""
    need(latest['candidate'] == CANDIDATE and identity(raw) == CANDIDATE,
         'exact current numeric candidate')
    bindings = source_proof(root)
    owners = latest['placement']['owner_byte_audit']
    regions, pools = [], []
    for name, layout in LAYOUTS.items():
        rows = [r for r in owners if r['name'] == name]
        need(len(rows) == 1, 'one latest actual numeric owner: ' + name)
        owner = rows[0]
        payload = donor.chunk(raw, owner['address'], owner['size'])
        found, summary = decode_level_pool(payload, owner, layout)
        regions.extend(found)
        pools.append(summary)
    rows = [r for r in owners if r['name'] == S39]
    need(len(rows) == 1, 'one latest actual Stage39 owner')
    metadata = None
    if (root / S39_METADATA).exists():
        saved = fixed_file(root, S39_METADATA)
        need(identity(saved) == S39_METADATA_ID, 'fixed original Stage39 metadata')
        bindings[S39_METADATA] = identity(saved)
        metadata = json.loads(saved)
    owner = rows[0]
    found, summary = stage39_regions(donor.chunk(raw, owner['address'], owner['size']), owner, metadata)
    regions.extend(found)
    pools.append(summary)
    diagnostics = [dict(owner='species_surface_tutor', status='UNCLASSIFIED_CONSUMER_STRIDE_UNPROVEN',
                        serializer_stride=16, fixed_upstream_num_move_tutors=152,
                        fixed_upstream_u32_array_stride=20,
                        stage39_stride_patch_declared=True,
                        hit_species_row=348, hit_row_byte_offset=8, physical_u32_word=2,
                        hit_kind='THUMB_BL_SHAPE', old_formal_legacy_table_gate_slots=64,
                        old_formal_observation_is_current_candidate_acceptance=False,
                        current_supply_wrapper_abi_verified=False,
                        direct_current_consumer_root_witness=False,
                        reason_ja='Stage39のstride16 patchを旧formalで確認したが、hitは物理row上位64bit側の第3u32。旧table pathはtutor<64で当該wordを読まない。入口の供給wrapperと現候補の直接consumer-root証拠が未確認なので1件を未知として保持し、機能不具合や全範囲安全を主張しない。')]
    return regions, dict(bindings=bindings, diagnostics=diagnostics, pools=pools,
                         status='PASS_FIXED_LEGACY_LEVEL_NUMERIC_TYPES',
                         candidate=CANDIDATE, full_rom_inventory_reused=True,
                         native_processes=0, arm_compiles=0, accepted_source_regenerations=0,
                         rom_writes=0, donor_leased=False, donor_eligible=False,
                         indirect_reference_completeness_claimed=False)
