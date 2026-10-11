#!/usr/bin/env python3
"""選定窓の音声originを固定WAV・全assetへ束縛する。readerや空容量は推定しない。"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'c75f352304d529f6ba92d4f74b9cf8b5c3810788'
SYMBOL = 'DirectSoundWaveData_unused_sc88pro_unison_slap'
WAV = 'sound/direct_sound_samples/unused_sc88pro_unison_slap.wav'
START = 0x08471C78
FOLLOWING = 0x08475274
HIT = 0x084723AF
HIT_ID = {'size': 4, 'sha256': 'eb72d696d22c970b1090b11a8020bfb44f42ecff189aaffc9b47eb75cbeb0993'}
CANDIDATE = {'size': 33554432, 'sha256': '0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583'}
BLOBS = {
    WAV: 'e9f48d6ff74573550e5815b991d719a0cdf08a05',
    'sound/direct_sound_data.inc': '98191db21902a49d9d20a2ec5442786fe41d85c0',
    'sound/voice_groups.inc': '13c8090a0670718b9686acc64d90ef844d529d13',
    'audio_rules.mk': '6b4e4afda840dbce45892a6b01c5e114deb1fd12',
    'tools/wav2agb/Makefile': 'a38f71758f173b1cff1b87f492477ec3a320a33a',
    'tools/wav2agb/converter.cpp': 'c826e0a784bcf673157ca55497bfdc4f5169d416',
    'tools/wav2agb/converter.h': 'df59ebe2d1206f5dcd0b4bae8c9afd9693462eb5',
    'tools/wav2agb/wav2agb.cpp': '2d4a84517e47d42abe3cf472871ad57960a10245',
    'tools/wav2agb/wav_file.cpp': '79cfed5d79bd39ca03926540d3c25bd0c38773ad',
    'tools/wav2agb/wav_file.h': 'cea278970de3c7c81a0374401fb84be4dc90e877',
}


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def identity(raw: bytes) -> dict:
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def blob(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def encode(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def u32(raw: bytes, offset: int = 0) -> int:
    need(type(offset) is int and 0 <= offset <= len(raw) - 4, 'u32範囲')
    return struct.unpack_from('<I', raw, offset)[0]


def chunks(raw: bytes) -> list[tuple[bytes, bytes, int]]:
    """RIFFの全範囲を閉じる。切断・重複・未宣言末尾を黙認しない。"""
    need(12 <= len(raw) <= 1_000_000, 'WAV有限長')
    need(raw[:4] == b'RIFF' and raw[8:12] == b'WAVE', 'RIFF/WAVE magic')
    need(u32(raw, 4) + 8 == len(raw), 'RIFF全長')
    offset, seen, result = 12, set(), []
    while offset < len(raw):
        need(offset + 8 <= len(raw), 'chunk header切断')
        tag, size = raw[offset:offset + 4], u32(raw, offset + 4)
        end = offset + 8 + size
        need(end + (size & 1) <= len(raw), 'chunk body/pad切断')
        need(tag not in seen, 'chunk重複')
        seen.add(tag)
        result.append((tag, raw[offset + 8:end], offset + 8))
        offset = end + (size & 1)
    need(offset == len(raw), 'chunk末尾')
    return result


def convert_pcm(raw: bytes) -> tuple[bytes, dict]:
    """固定wav2agb -bの独立整数対照。単音PCM8/16と既知chunkに限定。"""
    rows = chunks(raw)
    fields = {tag: value for tag, value, _ in rows}
    need(set(fields) <= {b'fmt ', b'data', b'smpl', b'agbp', b'agbl', b'LIST', b'JUNK'}, '未知chunk')
    need(b'fmt ' in fields and b'data' in fields, 'fmt/data必須')
    fmt, samples = fields[b'fmt '], fields[b'data']
    need(len(fmt) in (16, 18), 'fmt長')
    if len(fmt) == 18:
        need(fmt[16:] == b'\0\0', 'fmt拡張未対応')
    tag, channels, rate, byte_rate, align, bits = struct.unpack('<HHIIHH', fmt[:16])
    need(tag == 1 and channels == 1 and bits in (8, 16), '単音PCM8/16のみ')
    need(rate > 0 and align == bits // 8 and byte_rate == rate * align, 'PCM形式整合')
    need(len(samples) > 0 and len(samples) % align == 0, 'PCM frame切断')
    count = len(samples) // align
    loop_enabled, loop_start, loop_end, key, fraction = False, 0, count, 60, 0
    if b'smpl' in fields:
        smpl = fields[b'smpl']
        need(len(smpl) >= 36, 'smpl切断')
        key, fraction, loops, extra = u32(smpl, 12), u32(smpl, 16), u32(smpl, 28), u32(smpl, 32)
        need(key <= 127 and loops <= 1 and extra == 0 and len(smpl) == 36 + loops * 24, 'smpl有限形式')
        if loops:
            need(u32(smpl, 40) == 0, '前方向loopのみ')
            loop_start, inclusive_end = u32(smpl, 44), u32(smpl, 48)
            need(inclusive_end < 0xFFFFFFFF, 'loop end overflow')
            loop_end = min(inclusive_end + 1, count)
            need(loop_start < loop_end, 'loop範囲')
            loop_enabled = True
    pitch = 0
    if b'agbp' in fields:
        need(len(fields[b'agbp']) == 4, 'agbp長')
        pitch = u32(fields[b'agbp'])
    if not pitch:
        need(key == 60 and fraction == 0 and rate <= 0xFFFFFFFF // 1024, '推測pitch禁止')
        pitch = rate * 1024
    header_end = loop_end
    if b'agbl' in fields:
        need(len(fields[b'agbl']) == 4, 'agbl長')
        header_end = u32(fields[b'agbl']) or loop_end
    # agblは元headerの再現情報。payload長と同一へ「修正」しない。
    if bits == 8:
        pcm = bytes(v ^ 0x80 for v in samples[:loop_end])
    else:
        pcm = bytes((value[0] // 256) & 0xFF for value in struct.iter_unpack('<h', samples[:loop_end * 2]))
    header = struct.pack('<IIII', 0x40000000 if loop_enabled else 0, pitch, loop_start, header_end)
    payload = header + pcm
    result = payload + b'\0' * (-len(payload) % 4)
    return result, dict(format='PCM_S8',input_bits=bits,rate=rate,input_samples=count,
        loop_enabled=loop_enabled,loop_start=loop_start,payload_samples=loop_end,
        header_samples=header_end,header_and_payload_count_match=header_end == loop_end,
        pitch=pitch,padding_bytes=len(result)-len(payload),wav_identity=identity(raw),
        pcm_identity=identity(pcm),asset_identity=identity(result),
        chunks=[dict(id=t.decode('ascii'),offset=o,**identity(v)) for t,v,o in rows])


def compare_asset(raw: bytes, generated: bytes, origin: int, start: int, end: int,
                  expected_hit: dict) -> dict:
    """明示した有限assetとhitだけを比較する。全ROMscanはしない。"""
    need(all(type(x) is int for x in (origin, start, end)), 'address型')
    need(0x08000000 <= start < end <= 0x08000000 + len(raw), 'ROM slice範囲')
    need(end - start == len(generated), 'asset extent不一致')
    need(start + 16 <= origin and origin + 4 <= end, 'hitがpayload範囲外')
    segment = raw[start-0x08000000:end-0x08000000]
    need(segment == generated, '現候補全asset不一致')
    hit = segment[origin-start:origin-start+4]
    need(identity(hit) == expected_hit, '保存hit全4byte不一致')
    flags, pitch, loop_start, samples = struct.unpack_from('<IIII', generated)
    need(flags in (0, 0x40000000), '非圧縮音声header')
    need(origin + 4 <= start + 16 + samples, 'hitがheader sample範囲外')
    return dict(start=start,end_exclusive=end,**identity(segment),origin=origin,
        hit_identity=identity(hit),sample_index=origin-start-16,sample_count=4,
        flags=flags,pitch=pitch,loop_start=loop_start,header_samples=samples,
        current_candidate_asset_bound=True,actual_consumer_proven=False,
        formal_classification_changes=0,donor_safe_bytes=0,
        unused_name_proves_unreachable=False,rom_writes=0,save_writes=0)


def source_contract(data: dict[str, bytes]) -> dict:
    need(set(data) == set(BLOBS), '固定source集合')
    for path, raw in data.items():
        need(blob(raw) == BLOBS[path], '固定公開blob: ' + path)
    include = data['sound/direct_sound_data.inc'].decode()
    declaration = SYMBOL + '::\n\t.incbin "' + WAV[:-4] + '.bin"'
    need(include.count(declaration) == 1, 'asset定義の一意なincbin')
    rules = data['audio_rules.mk'].decode()
    need('$(SOUND_BIN_DIR)/%.bin: sound/%.wav\n\t$(WAV2AGB) -b $< $@' in rules, '実非圧縮build rule')
    return {path: dict(repository='pret/pokefirered',commit=SOURCE,git_blob=BLOBS[path],**identity(raw))
            for path,raw in sorted(data.items())}
