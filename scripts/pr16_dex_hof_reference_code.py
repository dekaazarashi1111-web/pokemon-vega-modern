#!/usr/bin/env python3
"""明示script根から直列Thumb命令だけ型付けし、別表consumerの誤採用を拒否。"""
from __future__ import annotations
import hashlib
import json
import struct
from pathlib import Path

import pr16_dex_hof_donor as d
from pr16_dex_hof_reference_data import CANDIDATE

ROOT = Path(__file__).resolve().parents[1]
REVIEW = 'content/modernization/pr16_dex_hof_reference_code_review.json'
REVIEW_ID = dict(size=18476, sha256='d477ad5a9d39438303a48516602efa7a466f473ca3e3969ee4d5eb8942a4c302')
need, identity, chunk = d.need, d.identity, d.chunk


def source_proof(root=ROOT):
    file = root / REVIEW
    need(file.is_file() and not file.is_symlink(), 'regular fixed code review')
    raw = file.read_bytes()
    need(identity(raw) == REVIEW_ID, 'immutable code and negative tutor review')
    review = json.loads(raw)
    need(review['target_current_candidate'] == CANDIDATE, 'code review current candidate')
    bindings = {REVIEW: identity(raw)}
    for name, expected in review['sources'].items():
        file = root / name
        need(file.is_file() and not file.is_symlink(), 'regular fixed code source')
        raw = file.read_bytes()
        need(identity(raw) == {k: expected[k] for k in ('size', 'sha256')} and
             hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() ==
             expected['git_blob_sha'], 'whole actual code source binding')
        bindings[name] = {k: expected[k] for k in ('size', 'sha256', 'git_blob_sha')}
    return review, bindings


def thumb_bl(raw, address):
    need(address % 2 == 0 and len(raw) == 4, 'aligned complete Thumb BL instruction')
    first, second = struct.unpack('<HH', raw)
    need(first & 0xF800 == 0xF000 and second & 0xF800 == 0xF800,
         'ARMv4T two-halfword BL only')
    displacement = ((first & 0x7FF) << 12) | ((second & 0x7FF) << 1)
    if displacement & (1 << 22):
        displacement -= 1 << 23
    return address + 4 + displacement


def entry_sequence(raw, address, targets, literal_address):
    """root PUSH→BL→BL→LDRの12byte限定。通常nm/.text全体は証拠にしない。"""
    need(address % 2 == 0 and len(raw) == 12 and len(targets) == 2,
         'exact rooted instruction extent')
    push = int.from_bytes(raw[:2], 'little')
    need(push & 0xFE00 == 0xB400 and push & 0x100 and push & 0xFF,
         'entry PUSH includes LR and nonempty register frame')
    observed = [thumb_bl(raw[2:6], address + 2), thumb_bl(raw[6:10], address + 6)]
    need(observed == targets and all(d.BASE <= a < d.BASE + 33554432 and
         not d.DONOR_LO <= a < d.DONOR_HI for a in observed), 'both typed callees outside donor')
    opcode = int.from_bytes(raw[10:12], 'little')
    need(opcode & 0xF800 == 0x4800, 'literal-load instruction, not literal data')
    slot = ((address + 10 + 4) & ~3) + (opcode & 255) * 4
    need(slot == literal_address and not address <= slot < address + len(raw),
         'separate aligned literal pool slot')
    return dict(address=address, **identity(raw), branch_targets=observed, literal_address=slot,
                exact_instruction_sizes=[2, 4, 4, 2])


def _code_regions(raw, latest, inherited, review):
    owners = {o['name']: o for o in latest['placement']['owner_byte_audit']}
    for expected in review['current_checkpoint_owner_bindings']:
        owner = owners.get(expected['name'])
        need(owner and owner['address'] == expected['address'] and owner['size'] == expected['size'] and
             owner['after_sha256'] == expected['current_checkpoint_after_sha256'] == expected['sha256'],
             'latest actual code/table owner')
        need(identity(chunk(raw, owner['address'], owner['size'])) ==
             {k: expected[k] for k in ('size', 'sha256')}, 'whole actual code/table bytes')
    d.signed(raw, review['minimal_old_formal_region_witnesses'])
    tutor = review['tutor_hit']
    need(next(h for h in inherited['hits'] if h['address'] == tutor['address']) == tutor and
         not tutor['accepted'], 'T09 upper word remains exact unknown')
    chain = review['root_chain']
    need(d.u32(raw, chain[0]['from'] + 4) == chain[0]['to'], 'redirected tutor wrapper root')
    literals = next(w for w in review['minimal_old_formal_region_witnesses']
                    if w['label'] == 'wrapper_plc2_image_and_reader_literals')
    need(d.u32(raw, literals['address']) == chain[2]['image'] and
         d.u32(raw, literals['address'] + 4) == chain[2]['reader'] and
         chain[2]['image'] != owners['species_surface_tutor']['address'],
         'current reader receives PLC2, not legacy T09 table')
    need(d.u32(raw, chain[-1]['old_formal_legacy_root_site']) == chain[-1]['observed_target'] and
         chain[-1]['observed_target'] != chain[-1]['does_not_equal_t09_root'],
         'no stale T09 pointer inference')
    code = review['stage74_separate_candidate']
    # 歴史的512byteの窓は後続hook改変を含む。現在も一致する64byteだけを束縛する。
    d.signed(raw, code['abi_entry_provenance']['exact_function_prefix_match'])
    d.signed(raw, code['entry_instruction_windows'])
    d.signed(raw, code['entry_contiguous_window'])
    d.signed(raw, code['literal_witness'])
    d.signed(raw, code['source_script_root']['script_window'])
    call = code['source_script_root']['callnative']
    d.signed(raw, call)
    call_raw = chunk(raw, call['address'], 5)
    need(call_raw[0] == 0x23 and int.from_bytes(call_raw[1:], 'little') ==
         call['target'] == code['symbol_address'] | 1, 'complete source CALLNATIVE root')
    instructions = code['entry_instruction_windows']
    proof = entry_sequence(chunk(raw, code['symbol_address'], 12), code['symbol_address'],
                           [r['target'] for r in instructions if r['kind'] == 'THUMB_BL'],
                           code['literal_witness']['address'])
    need(d.u32(raw, code['literal_witness']['address']) == code['literal_witness']['value'] == 0x02037004,
         'separate literal is pinned EWRAM, never counted as code')
    hit = code['hit']
    need(next(h for h in inherited['hits'] if h['address'] == hit['address']) == hit and
         hit['address'] == code['symbol_address'] + 7 and hit['size'] == 4,
         'exact original odd-byte cross-instruction hit')
    evidence = dict(fixed_review=REVIEW, rooted_entry=proof, script_root=call,
                    actual_owner=code['current_owner'], hit=hit,
                    literal_classification_claimed=False, full_story_reachability_claimed=False)
    region = d.TypedRegion(code['symbol_address'] + 6, code['symbol_address'] + 12,
                           'rooted_thumb_instruction_crossing', evidence)
    negative = dict(status='CURRENT_WRAPPER_READS_PLC2_NOT_T09_UPPER_WORD',
        hit=tutor, classified=False, direct_legacy_upper_word_consumer_proven=False,
        root_chain=chain, fixed_review=REVIEW, donor_leased=False)
    return [region], dict(status='PASS_ROOTED_INSTRUCTION_AND_NEGATIVE_TUTOR_WITNESS',
                          instruction=proof, tutor_negative=negative)


def code_regions(raw, latest, inherited, root=ROOT):
    need(identity(raw) == latest['candidate'] == inherited['candidate'] == CANDIDATE,
         'exact current candidate before instruction classification')
    review, bindings = source_proof(root)
    regions, proof = _code_regions(raw, latest, inherited, review)
    proof['source_bindings'] = bindings
    return regions, proof
