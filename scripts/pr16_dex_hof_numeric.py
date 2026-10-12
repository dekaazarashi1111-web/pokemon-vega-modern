#!/usr/bin/env python3
"""Reuse the measured all-byte inventory; prove PLR1 numeric consumers without ROM/native replay."""
from __future__ import annotations
import copy
import hashlib
import json
import struct
from pathlib import Path
import pr16_dex_hof_donor as donor

ROOT = Path(__file__).resolve().parents[1]
need, identity = donor.need, donor.identity
OWNER = 'pr16_learnset_runtime_two_entrypoints'
CP = 'content/modernization/pr16_learnset_runtime_checkpoint.json'
EVIDENCE = 'content/modernization/pr16_learnset_runtime_evidence/'
PINNED_CP = {'size': 19999, 'sha256': '6f84300daaf97649e29438bf38e3f17d990ba1e98266a33abc0939227baac6ff'}
SOURCES = ('tools/pr16_learnset_runtime.py', 'scripts/pr16_learnset_runtime_link.py',
           'src/modernization/pr16_learnset_game.c', 'src/modernization/pr16_learnset_runtime.c',
           'src/modernization/pr16_learnset_runtime.h', 'src/modernization/pr16_learnset_owner.c',
           'src/modernization/pr16_learnset_owner.h')


INHERITED_PINNED = {'content/modernization/pr16_dex_hof_capacity_checkpoint.json': {'size': 860558, 'sha256': '616d587c9d4ca8699efcf7adfe69be659371b3c60b4348266fbdaee0ff366d45'}, 'content/modernization/pr16_dex_hof_generation_writer_checkpoint.json': {'size': 388088, 'sha256': '2aa483a860c7f5bc4919f6a3f11c74e3d209399059e8febbd63f3baaa16a8d49'}}

def load_inherited(root=ROOT):
    values = []
    for path, expected in INHERITED_PINNED.items():
        p = root / path
        need(p.is_file() and not p.is_symlink(), 'regular immutable inherited proof')
        raw = p.read_bytes()
        need(identity(raw) == expected, 'immutable inherited proof identity')
        values.append(json.loads(raw))
    return values[0]['typed_audit'], values[1]


def source_proof(root=ROOT):
    raw = (root / CP).read_bytes()
    need(identity(raw) == PINNED_CP, 'fixed original PLR1 checkpoint')
    cp = json.loads(raw)
    bindings = {CP: identity(raw)}
    for path in SOURCES:
        p = root / path
        need(p.is_file() and not p.is_symlink(), 'regular original source')
        observed = identity(p.read_bytes())
        need(observed == cp['verification']['code_bindings'][path], 'original PLR1 generator/consumer changed: ' + path)
        bindings[path] = observed
    docs = {}
    for name in ('receipt.json', 'link.json'):
        path = EVIDENCE + name
        p = root / path
        need(p.is_file() and not p.is_symlink(), 'regular original proof')
        raw = p.read_bytes()
        need(identity(raw) == cp['proof_bindings'][name], 'original PLR1 proof changed')
        bindings[path] = identity(raw)
        docs[name] = json.loads(raw)
    return docs['receipt.json'], docs['link.json'], bindings


def numeric_regions(bundle, receipt, link, owner):
    """Exact compose bytes + linked reader ABI + full coverage, including each terminator."""
    address = donor.BASE + link['start']
    need((owner['name'], owner['address'], owner['size'], owner['after_sha256']) ==
         (OWNER, address, len(bundle), identity(bundle)['sha256']), 'latest actual byte-owner matches accepted bundle')
    need(identity(bundle) == link['bundle'] and receipt['image'] == link['image'], 'whole accepted linked bundle')
    image = bundle[:receipt['size']]
    need(identity(image) == receipt['image'] and len(image) == receipt['size'], 'whole accepted PLR1 image')
    need((link['code_start'], link['code_end']) == (address + len(image), address + len(bundle)), 'image/code extent separation')
    need(len(image) >= 32, 'whole PLR1 header')
    magic, version, count, policy, index, level, machine, total, reserved = struct.unpack_from('<4sHHIIIIII', image)
    need((magic, version, count, policy, index, level, total, reserved) ==
         (b'PLR1', 1, 1671, 32, 1704, 15072, len(image), 0), 'exact PLR1 consumer header')
    need((receipt['format'], receipt['species_count'], receipt['header_size'], receipt['entry_size'],
          receipt['policy_offset'], receipt['index_offset'], receipt['level_offset'], receipt['machine_offset']) ==
         ('PLR1', count, 32, 8, policy, index, level, machine), 'compose receipt and consumer ABI agree')
    need(machine % 4 == 0 and level < machine and machine + 1483 * 16 == total,
         'whole numeric/machine pool bounds')
    need(image[policy + count:index] == bytes(index - policy - count), 'excluded policy alignment padding')
    expected = [('ACCEPTED_PARENT', 'level_up.bin'), ('FLOETTE_DELTA', 'floette.level_up.bin'),
                ('ACCEPTED_PARENT', 'machine.bin'), ('FLOETTE_DELTA', 'floette.machine.bin')]
    copies = receipt['copies']
    need([(r['arena'], r['file']) for r in copies] == expected, 'exact four compose source arenas')
    for row in copies:
        start, size = row['image_offset'], row['size']
        need(type(start) is int and type(size) is int and size > 0 and 0 <= start <= total - size,
             'bounded compose copy extent')
        need(identity(image[start:start + size]) == {k: row[k] for k in ('size', 'sha256')}, 'all compose copy bytes')
    parent, delta, machines, machine_delta = copies
    end = delta['image_offset'] + delta['size']
    need(parent['image_offset'] == level and parent['size'] % 3 == 0 and delta['size'] % 3 == 0 and
         delta['image_offset'] == level + parent['size'] and end <= machine and machine - end < 4 and
         machines['image_offset'] == machine and machines['size'] == 1482 * 16 and
         machine_delta['image_offset'] == machine + machines['size'] and machine_delta['size'] == 16,
         'exact contiguous compose pools; padding not typed')
    need(image[end:machine] == bytes(machine - end), 'excluded inter-pool alignment padding')
    policies = image[policy:policy + count]
    need(len(policies) == count and all(1 <= x <= 7 for x in policies) and policies.count(1) == 1483,
         'all explicit owner policies')
    spans, slots = [], set()
    for sid, action in enumerate(policies):
        start, length, slot = struct.unpack_from('<IHH', image, index + sid * 8)
        if action != 1:
            need((start, length, slot) == (0xffffffff, 0, 0xffff), 'identity-only sentinel has no numeric payload')
            continue
        stop = start + 3 * (length + 1)
        need(length <= 40 and 0 <= slot < 1483 and level <= start < stop <= end and
             (start - level) % 3 == 0, 'whole 3-byte owner span')
        source = delta if sid == 1029 else parent
        need(source['image_offset'] <= start < stop <= source['image_offset'] + source['size'],
             'exact parent or Floette source arena')
        need(image[stop - 3:stop] == b'\0\0\xff', 'numeric terminator')
        need(all(1 <= move <= 1062 and 1 <= lv <= 100 for move, lv in
                 struct.iter_unpack('<HB', image[start:stop - 3])), 'U16 move/U8 level typed rows')
        need(slot not in slots and (slot == 1482) == (sid == 1029), 'unique machine slot and Floette source')
        slots.add(slot)
        spans.append(dict(species_id=sid, address=address + start, size=stop - start,
                          row_count=length, sha256=identity(image[start:stop])['sha256']))
    spans.sort(key=lambda r: r['address'])
    need(len(spans) == receipt['learning_owners'] == 1483 and receipt['identity_only_preserved'] == 188 and
         max(r['row_count'] for r in spans) == receipt['max_level_rows'], 'all accepted owner counters')
    need(spans[0]['address'] == address + level and spans[-1]['address'] + spans[-1]['size'] == address + end and
         all(a['address'] + a['size'] == b['address'] for a, b in zip(spans, spans[1:])),
         'complete nonoverlapping numeric coverage; no gaps or unused bytes')
    consumers = dict(generator='tools/pr16_learnset_runtime.py#compose',
                     reader='src/modernization/pr16_learnset_runtime.c#Pr16ReadLearnsetRuntime',
                     getter='src/modernization/pr16_learnset_runtime.c#Pr16RuntimeLevelMoves',
                     wrapper='src/modernization/pr16_learnset_game.c#Pr16_GameGetLevelUpMovesBySpecies',
                     numeric_encoding='LE_U16_MOVE_U8_LEVEL; terminal MOVE0_LEVEL255; no pointer interpretation',
                     image=dict(address=address, **identity(image)),
                     consumer_code=dict(address=link['code_start'], **identity(bundle[len(image):])),
                     bundle=dict(address=address, **identity(bundle)),
                     header=dict(address=address, **identity(image[:32])),
                     policy=dict(address=address + policy, **identity(policies)),
                     index=dict(address=address + index, **identity(image[index:level])),
                     owner=OWNER, owner_count=len(spans), identity_only_count=188,
                     full_pool_covered=True, source_proof=CP)
    regions = []
    for source in (parent, delta):
        start, size = source['image_offset'], source['size']
        rows = [s for s in spans if address + start <= s['address'] < address + start + size]
        proof = dict(consumers, pool=dict(address=address + start, size=size, sha256=source['sha256']),
                     compose_source={k: source[k] for k in ('arena', 'file', 'image_offset', 'size', 'sha256')},
                     row_spans=rows)
        regions.append(donor.TypedRegion(address + start, address + start + size, 'plr1_numeric', proof))
    return regions


def bundle_inventory(bundle, address):
    """Repeat only the unchanged bundle scope; retain all external/boundary origins from prior full scan."""
    hits = []
    for at in range(len(bundle) - 3):
        target = donor.canonical(struct.unpack_from('<I', bundle, at)[0])
        if donor.DONOR_LO <= target < donor.DONOR_HI:
            hits.append(dict(address=address + at, target=target, kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS',
                             **identity(bundle[at:at + 4])))
    for at in range(address % 2, len(bundle) - 3, 2):
        a, b = struct.unpack_from('<HH', bundle, at)
        if a & 0xf800 == 0xf000 and b & 0xf800 == 0xf800:
            displacement = (a & 0x7ff) << 12 | (b & 0x7ff) << 1
            if displacement & 1 << 22:
                displacement -= 1 << 23
            target = address + at + 4 + displacement
            if donor.DONOR_LO <= target < donor.DONOR_HI:
                hits.append(dict(address=address + at, target=target, kind='THUMB_BL_SHAPE',
                                 **identity(bundle[at:at + 4])))
    return hits


def extend(prior, latest, bundle, root=ROOT):
    need(prior['candidate'] == latest['candidate'] and not prior['donor_leased'] and not prior['donor_eligible'],
         'exact retained candidate without donor authority')
    receipt, link, sources = source_proof(root)
    owners = latest['placement']['owner_byte_audit']
    found = [r for r in owners if r['name'] == OWNER]
    need(len(found) == 1, 'one latest measured PLR1 owner')
    owner = found[0]
    regions = numeric_regions(bundle, receipt, link, owner)
    inside = [r for r in prior['hits'] if donor.contains(owner['address'], owner['address'] + owner['size'], r['address'], r['size'])]
    rescanned = bundle_inventory(bundle, owner['address'])
    need(donor.compare_inventory(rescanned, dict(candidate=prior['candidate'], hits=inside))['same_inventory'],
         'all bundle byte/mirror/Thumb scan identities retained')
    result = copy.deepcopy(prior)
    changed = []
    for i, hit in enumerate(result['hits']):
        if hit['accepted']:
            continue
        classification = copy.deepcopy(donor.classify_hits([hit], regions, owners)[0])
        if not classification['accepted']:
            continue
        classification.pop('reason', None)
        classification.pop('owner_candidates', None)
        at = hit['address'] - owner['address']
        need(identity(bundle[at:at + hit['size']]) == {k: hit[k] for k in ('size', 'sha256')}, 'retained hit bytes')
        # Only the small containing row spans enter the public hit witness, not every species span.
        for proof in classification['evidence']:
            proof['row_spans'] = [r for r in proof['row_spans'] if r['address'] < hit['address'] + hit['size'] and hit['address'] < r['address'] + r['size']]
        result['hits'][i] = classification
        changed.append({k: hit[k] for k in ('address', 'size', 'sha256', 'kind', 'target')})
    need(len(prior['hits']) == prior['candidates'] == len(result['hits']), 'full prior inventory retained')
    result['source_bindings'].update(sources)
    result['unclassified'] = sum(not r['accepted'] for r in result['hits'])
    result['classified'] = len(result['hits']) - result['unclassified']
    result['classifications'] = dict(donor.collections.Counter(r['classification'] for r in result['hits']))
    result['numeric_extension'] = dict(status='PASS_EXACT_PLR1_SOURCE_AND_CONSUMER_CLASSIFICATION',
        changed_hits=changed, newly_classified=len(changed), all_prior_accepted_retained=True,
        full_rom_inventory_reused=True, bundle_rescan_bytes=len(bundle), current_rom_reconstruction=False,
        owner_after_sha256=owner['after_sha256'], source_bindings=sources,
        typed_pools=[dict(address=r.start, size=r.end-r.start, sha256=r.evidence['pool']['sha256']) for r in regions],
        excluded_alignment_bytes=1, original_artifact_reused=True,
        native_processes=0, arm_compiles=0, rom_writes=0, donor_leased=False,
        indirect_reference_completeness_claimed=False)
    return result
