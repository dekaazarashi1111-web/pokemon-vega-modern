#!/usr/bin/env python3
"""Fallback tailの読取専用・全候補型付き検証。ROM/生byteを書き出さない。"""
import argparse
import collections
import hashlib
import json
import struct
import zipfile
from pathlib import Path

B = 0x08000000
LO = 0x09FFFDC4
MAX_SIZE = 296
FORMAL_SHA = '06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5'
PROOF = Path(__file__).resolve().parents[1]/'content/modernization/pr16_dex_fallback_tail_lease.json'

def need(ok, label):
    if not ok:
        raise ValueError(label)

def digest(data):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

def literal_inventory(raw, lo, hi):
    result = []
    for high in (9, 11, 13):
        at = 0
        while True:
            end = raw.find(bytes([high]), at)
            if end < 0:
                break
            at = end + 1
            if end < 3:
                continue
            start = end - 3
            value = struct.unpack_from('<I', raw, start)[0]
            normalized = value - (high - 9) * 0x1000000
            if lo <= normalized < hi:
                result.append({'address': B + start, 'target': value})
    return sorted(result, key=lambda row: row['address'])

def branch_inventory(raw, lo, hi):
    result = []
    for at in range(0, len(raw) - 3, 2):
        high, low = struct.unpack_from('<HH', raw, at)
        if high & 0xF800 != 0xF000 or low & 0xF800 != 0xF800:
            continue
        relative = ((high & 0x7FF) << 12) | ((low & 0x7FF) << 1)
        if relative & (1 << 22):
            relative -= 1 << 23
        target = B + at + 4 + relative
        if lo <= target < hi:
            result.append({'address': B + at, 'target': target})
    return result

def dpcm_size(samples):
    blocks, last = divmod(samples, 64)
    return blocks * 33 + (0 if last == 0 else 1 if last == 1 else 1 + (last + 1) // 2)

def decode_dpcm(data, samples):
    # Independent random-index implementation of SoundMainRAM_Unk2.
    # A block is 33 bytes / 64 samples: initial byte, low nibble of byte1,
    # then high and low nibbles of bytes2..32. Byte1 high is not a sample.
    need(len(data) == dpcm_size(samples), 'minimal declared DPCM extent')
    delta = (0, 1, 4, 9, 16, 25, 36, 49, -64, -49, -36, -25, -16, -9, -4, -1)
    out = bytearray()
    for block in range((samples + 63) // 64):
        at = block * 33
        count = min(64, samples - block * 64)
        value = data[at]
        out.append(value)
        for index in range(1, count):
            byte = data[at + (index + 2) // 2]
            nibble = (byte >> (4 if index % 2 == 0 else 0)) & 15
            value = (value + delta[nibble]) & 255
            out.append(value)
    return bytes(out)

def decode_sprite(data, width=16, height=144):
    need(len(data) == width * height // 2 and width % 8 == height % 8 == 0, '4bpp tile extent')
    out = bytearray(width * height)
    at = 0
    for tile_y in range(height // 8):
        for tile_x in range(width // 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    byte = data[at]
                    at += 1
                    dst = (tile_y * 8 + y) * width + tile_x * 8 + x
                    out[dst] = byte & 15
                    out[dst + 1] = byte >> 4
    return bytes(out)

def normalized(target):
    return B + ((target - B) & 0x01FFFFFF)

def validate(raw, proof=None, size=None, require_formal=False):
    p = json.loads(PROOF.read_text()) if proof is None else proof
    need(len(raw) == 32 * 1024 * 1024, '32MiB ROM')
    if require_formal:
        need(hashlib.sha256(raw).hexdigest() == FORMAL_SHA, 'formal ROM identity')
    scope = p['scope']
    need(scope['base'] == LO and 0 < scope['size'] <= MAX_SIZE and scope['end_exclusive'] == LO + scope['size'], 'bounded fallback scope')
    if size is None:
        size = scope['size']
    need(0 < size <= scope['size'], 'prefix shrink only')
    hi = LO + size
    literals = [x for x in p['candidates'] if LO <= normalized(x['target']) < hi]
    branches = [x for x in p['branch_candidates'] if LO <= x['target'] < hi]
    take = lambda rows: sorted(({'address': x['address'], 'target': x['target']} for x in rows), key=lambda x: x['address'])
    need(literal_inventory(raw, LO, hi) == take(literals), 'complete all-byte 3-mirror literal inventory')
    need(branch_inventory(raw, LO, hi) == take(branches), 'complete aligned ThumbBL inventory')
    need(scope['literal_candidates'] == len(p['candidates']) and scope['thumb_bl_candidates'] == len(p['branch_candidates']), 'proof inventory counters')
    def chunk(address, length):
        need(B <= address < address + length <= B + len(raw), 'ROM window range')
        return raw[address - B:address - B + length]
    def signed(obj):
        if isinstance(obj, dict):
            if all(key in obj for key in ('address', 'size', 'sha256')):
                need(digest(chunk(obj['address'], obj['size'])) == {key: obj[key] for key in ('size', 'sha256')}, 'whole signed window')
            for value in obj.values():
                signed(value)
        elif isinstance(obj, list):
            for value in obj:
                signed(value)
    active = {row['root'] for row in literals + branches}
    roots = {row['address']: row for row in p['roots']}
    need(len(roots) == len(p['roots']) == p['root_count'], 'unique root inventory')
    need({row['root'] for row in p['candidates'] + p['branch_candidates']} == set(roots), 'no unreferenced or missing typed roots')
    tail = chunk(LO, size)
    need(tail == b'\xff' * size, 'tail prefix remains unallocated FF preimage')
    if size == scope['size']:
        need(digest(tail) == {key: p['tail_preimage'][key] for key in ('size', 'sha256')}, 'tail preimage digest')
    for address in sorted(active):
        root = roots[address]
        signed(root)
        data = chunk(address, root['size'])
        if root['kind'] in ('pcm8', 'dpcm4'):
            fields = struct.unpack_from('<HHIII', data)
            need(fields == tuple(root[key] for key in ('wave_type', 'wave_status', 'wave_frequency', 'wave_loop_start', 'decoded_size')), 'complete WaveData header')
            need(root['wave_type'] == (1 if root['kind'] == 'dpcm4' else 0), 'wave decoder type')
            need(root['wave_status'] in (0, 0x4000) and 0 <= root['wave_loop_start'] < root['decoded_size'], 'wave loop bounds')
            need(root['header']['address'] == address and root['header']['size'] == 16, 'signed full wave header')
            need(root['refs'], 'rooted WaveData')
            for ref in root['refs']:
                need(struct.unpack('<I', chunk(ref['address'], 4))[0] == ref['value'] == address, 'actual WaveData pointer')
                tone = ref['tone_record']
                need(tone['address'] + 4 == ref['address'] and tone['size'] == 12, 'ToneData pointer field')
                fields = struct.unpack('<4BI4B', chunk(tone['address'], 12))
                need(list(fields) == tone['fields'], 'complete ToneData descriptor')
                need(fields[0] & 0xC7 == 0 and fields[1] <= 127 and fields[4] == address, 'direct-sound ToneData root')
            decoded = decode_dpcm(data[16:], root['decoded_size']) if root['kind'] == 'dpcm4' else data[16:]
        elif root['kind'] == 'raw_4bpp_sprite_frames':
            need(root['width'] == 16 and root['height'] == 144 and root['frame_count'] == 9 and root['frame_size'] == 128, 'source 9-frame 16x16 sprite shape')
            table = root['frame_table']
            need(table['size'] == root['frame_count'] * 8, 'complete SpriteFrameImage table')
            for index, frame in enumerate(root['frames']):
                need(frame['address'] == address + index * 128 and frame['size'] == 128, 'contiguous frame pixels')
                pointer, length, padding = struct.unpack('<IHH', chunk(table['address'] + 8 * index, 8))
                need((pointer, length, padding) == (frame['address'], 128, 0), 'typed SpriteFrameImage data/size')
            template = root['sprite_template']
            fields = struct.unpack('<HHIIIII', chunk(template['address'], 24))
            need(list(fields) == template['fields'] and fields[0] == 65535 and fields[4] == table['address'], 'SpriteTemplate images field')
            refs = root['template_refs']
            need(refs, 'SpriteTemplate rooted reference')
            for ref in refs:
                need(struct.unpack('<I', chunk(ref['address'], 4))[0] == ref['value'] == template['address'], 'template pointer-table row')
            pointer_table = root['template_pointer_table']
            need(pointer_table['row_index'] == 17 and pointer_table['address'] + 4 * 17 == refs[0]['address'], 'source FLDEFFOBJ_UNUSED_GRASS index17')
            need(pointer_table['root_sites'], 'rooted field-effect pointer table')
            for ref in pointer_table['root_sites']:
                need(struct.unpack('<I', chunk(ref['address'], 4))[0] == ref['value'] == pointer_table['address'], 'actual field-effect table root')
            animation = root['animation']
            need(struct.unpack('<I', chunk(fields[3], 4))[0] == animation['address'], 'animation table to commands')
            cmds = list(struct.unpack('<20H', chunk(animation['address'], 40)))
            need(cmds == [value for pair in animation['commands'] for value in pair], 'complete source animation commands')
            need(animation['commands'] == [[0, 10]] + [[index, 4] for index in range(1, 9)] + [[65534, 7]], 'frames0..8 then jump7')
            decoded = decode_sprite(data)
            need(root['source_png']['decoded_sha256'] == root['decoded_sha256'] and root['source_png']['all_1152_encoded_bytes_match'], 'whole independently matched source sprite')
        else:
            raise ValueError('unrecognized fallback typed root')
        need(digest(decoded) == {'size': root['decoded_size'], 'sha256': root['decoded_sha256']}, 'whole declared decoded payload')
    for row in literals:
        root = roots[row['root']]
        offset = 0 if root['kind'] == 'raw_4bpp_sprite_frames' else 16
        need(row['kind'] == root['kind'] and root['address'] + offset <= row['address'] and row['address'] + 4 <= root['address'] + root['size'], 'literal wholly inside typed data')
        need(row['encoded_offset'] == row['address'] - root['address'], 'exact encoded offset')
    for row in branches:
        root = roots[row['root']]
        need(root['kind'] == row['kind'] == 'dpcm4' and root['address'] + 16 <= row['address'] and row['address'] + 4 <= root['address'] + root['size'], 'BL wholly inside encoded DPCM')
    need(dict(collections.Counter(x['kind'] for x in p['candidates'])) == p['candidate_types'], 'literal type counts')
    need(dict(collections.Counter(x['kind'] for x in p['branch_candidates'])) == p['branch_candidate_types'], 'branch type counts')
    return {'status': 'PASS_TYPED_FALLBACK_TAIL_REFERENCE_CLASSIFICATION', 'address': LO, 'size': size, 'literal_candidates': len(literals), 'thumb_bl_candidates': len(branches), 'root_count': len(active), 'candidate_types': dict(collections.Counter(x['kind'] for x in literals)), 'branch_candidate_types': dict(collections.Counter(x['kind'] for x in branches)), 'unclassified_candidates': 0}

def read_rom(path):
    path = Path(path)
    if path.suffix.lower() == '.zip':
        with zipfile.ZipFile(path) as archive:
            return archive.read('candidate.gba')
    return path.read_bytes()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', help='読取専用ROMまたはcandidate.gbaを含むZIP')
    parser.add_argument('--proof', type=Path, default=PROOF)
    parser.add_argument('--size', type=int, help='監査済み296byteの先頭に縮小する場合だけ指定')
    parser.add_argument('--formal', action='store_true', help='正式ROM SHAも検証')
    args = parser.parse_args()
    print(json.dumps(validate(read_rom(args.rom), json.loads(args.proof.read_text()), args.size, args.formal), indent=2))
