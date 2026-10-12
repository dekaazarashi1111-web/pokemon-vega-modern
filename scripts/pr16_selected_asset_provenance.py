#!/usr/bin/env python3
"""選定4byteの入力系譜と所有境界。配置履歴を実asset readerと混同しない。"""
from __future__ import annotations
import struct
import pr16_selected_sound_roots as parent

BASE_HEAD='55f1e69e1c2a6b00a556c5e02662cb17ab61cc33'
BASE=parent.BASE
CANDIDATE=parent.CANDIDATE
TARGETS=parent.TARGETS
need,identity,encode=parent.need,parent.identity,parent.encode
MAX_ROM=32*1024*1024


def parse_ips(raw: bytes) -> dict:
    """順序付きIPS区間を保持。RLE0長/EOF末尾不正/ROM外書込は拒否する。"""
    need(type(raw) is bytes and raw.startswith(b'PATCH'),'IPS signature')
    cursor=5; records=[]
    while True:
        need(cursor+3<=len(raw),'IPS offset truncated')
        position=cursor;word=raw[cursor:cursor+3];cursor+=3
        if word==b'EOF':break
        need(len(records)<1000000 and cursor+2<=len(raw),'IPS bounded records/size')
        offset=int.from_bytes(word,'big');size=int.from_bytes(raw[cursor:cursor+2],'big');cursor+=2
        if size:
            need(cursor+size<=len(raw),'IPS literal truncated')
            payload=raw[cursor:cursor+size];cursor+=size;kind='literal'
        else:
            need(cursor+3<=len(raw),'IPS RLE truncated')
            size=int.from_bytes(raw[cursor:cursor+2],'big');cursor+=2
            need(size>0,'IPS RLE empty')
            payload=raw[cursor:cursor+1];cursor+=1;kind='rle'
        need(offset+size<=MAX_ROM,'IPS write outside ROM')
        records.append(dict(index=len(records),patch_offset=position,start=offset,end_exclusive=offset+size,
                            kind=kind,payload=payload))
    need(len(raw)-cursor in (0,3),'IPS invalid trailing bytes')
    truncate=int.from_bytes(raw[cursor:],'big') if len(raw)>cursor else None
    need(truncate is None or 0<truncate<=MAX_ROM,'IPS truncation bound')
    return dict(records=records,truncate=truncate,identity=identity(raw))


def source_slice(raw: bytes, offset: int, width: int=4) -> dict:
    need(type(offset) is int and type(width) is int and 0<=offset and width>0,'positive source slice')
    if offset+width>len(raw):return dict(present=False,source_size=len(raw))
    return dict(present=True,**identity(raw[offset:offset+width]))


def ips_target(parsed: dict, base: bytes, patched: bytes, offset: int, width: int=4) -> dict:
    """対象の各byteの最終writeだけを解決。未定義拡張paddingを勝手に埋めない。"""
    need(type(offset) is int and type(width) is int and 0<=offset<offset+width<=MAX_ROM and width<=256,'bounded IPS target')
    final=[None]*width; values=[base[offset+i] if offset+i<len(base) else None for i in range(width)]
    overlaps=[]
    for r in parsed['records']:
        lo,hi=max(offset,r['start']),min(offset+width,r['end_exclusive'])
        if lo>=hi:continue
        meta={k:r[k] for k in ('index','patch_offset','start','end_exclusive','kind')}
        meta['payload_identity']=identity(r['payload']);overlaps.append(meta)
        for at in range(lo,hi):
            i=at-offset;final[i]=r['index']
            values[i]=r['payload'][at-r['start']] if r['kind']=='literal' else r['payload'][0]
    trunc=parsed['truncate'];inside=trunc is None or offset+width<=trunc
    resolved=inside and all(v is not None for v in values)
    expected=bytes(values) if resolved else None
    actual=source_slice(patched,offset,width)
    return dict(offset=offset,width=width,overlapping_records=overlaps,last_writer_indices=final,
                within_declared_truncation=inside,fully_resolved=resolved,
                reconstructed_identity=identity(expected) if expected is not None else None,
                reference_slice=actual,reference_matches=bool(resolved and actual['present'] and expected==patched[offset:offset+width]),
                expansion_padding_inferred=False)


def owners_at(placement: dict, address: int, width: int=4) -> dict:
    need(type(address) is int and type(width) is int and BASE<=address<address+width<=BASE+MAX_ROM,'owner target bounds')
    allocation=placement['allocation']['allocations'];audit=placement['owner_byte_audit']
    names=[r['name'] for r in allocation]
    need(len(names)==len(set(names)) and len(audit)==len(names),'owner uniqueness')
    audited={r['name']:r for r in audit};need(set(audited)==set(names),'owner audit completeness')
    spans=[]
    for row in allocation:
        a,z=row['start'],row['end_exclusive'];seen=audited[row['name']]
        need(type(a) is int and type(z) is int and 0<=a<z<=MAX_ROM,'owner declared bound')
        need(seen['address']==BASE+a and seen['size']==z-a,'owner audit bound')
        spans.append((a,z,row,seen))
    spans.sort(key=lambda s:s[:2])
    need(all(l[1]<=r[0] for l,r in zip(spans,spans[1:])),'owner overlap forbidden')
    start=address-BASE;end=start+width;matches=[]
    for a,z,row,seen in spans:
        if a<end and start<z:
            matches.append(dict(name=row['name'],start=BASE+a,end_exclusive=BASE+z,
                                full_target_containment=a<=start and end<=z,
                                allocation_content_sha256=row['content_sha256'],
                                current_owner_sha256=seen['after_sha256'],
                                allocation_hash_is_current=row['content_sha256']==seen['after_sha256'],
                                owner_offset=start-a))
    return dict(address=address,width=width,owners=matches,
                fully_owned=len(matches)==1 and matches[0]['full_target_containment'],
                crossing_owner_boundary=bool(matches) and not(len(matches)==1 and matches[0]['full_target_containment']),
                free_space_proven=False,actual_asset_reader_proven=False)


def measure(base: bytes, patch: bytes, vega: bytes, checkpoint: dict, sound: dict) -> dict:
    need(checkpoint['candidate']==sound['candidate']==CANDIDATE,'current whole ROM identity')
    placement=checkpoint['placement'];need(identity(encode(placement))==sound['placement_identity'],'saved complete115owner placement')
    need(len(placement['allocation']['allocations'])==115,'current115owners')
    target_rows=sound['targets'];need([r['address'] for r in target_rows]==list(TARGETS),'saved three targets')
    parsed=parse_ips(patch);rows=[]
    for saved in target_rows:
        address=saved['address'];offset=address-BASE
        evidence=ips_target(parsed,base,vega,offset);modern=owners_at(placement,address)
        formal={k:saved[k] for k in ('size','sha256')}
        current_equals_vega=evidence['reference_slice'].get('present',False) and all(evidence['reference_slice'][k]==formal[k] for k in formal)
        clean=source_slice(base,offset)
        rows.append(dict(address=address,current_target_identity=formal,clean_slice=clean,ips=evidence,modernization=modern,
                         current_target_equals_vega=current_equals_vega,
                         current_target_equals_clean=clean.get('present',False) and all(clean[k]==formal[k] for k in formal),
                         actual_asset_reader_proven=False))
    return dict(schema_version=1,candidate=CANDIDATE,clean_identity=identity(base),ips_identity=identity(patch),vega_identity=identity(vega),
                inputs_are_originals=True,ips_record_count=len(parsed['records']),ips_truncate=parsed['truncate'],
                placement_identity=identity(encode(placement)),rows=rows,actual_asset_reader_proven=False,
                formal_classification_changes=0,formal_classified=789,formal_unclassified=85,selected_unknown_origins=6,donor_safe_bytes=0,
                limitations_ja=['選定各4byteの値/入力順序/現owner境界のみ。値一致は履歴の書込不存在証明ではない。',
                                'IPSの未定義拡張paddingは推測しない。未所有範囲もfreeではない。',
                                'asset境界・実caller/reader・間接参照網羅・donor退役権限は未証明。'])
