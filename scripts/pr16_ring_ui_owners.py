#!/usr/bin/env python3
"""保存resource graphを固定JP symbolとUI構造体へ結合。live allocationの受入ではない。"""
from __future__ import annotations
import base64
import copy
import ctypes
import hashlib
import json
import re
import sys
from pathlib import PurePosixPath

BASE='1cbae24d59fec4d84a851fed3bc889a664391f40'
SLUG='pr16-ring-ui-owners'
TASK='PR-P08-7-RING-UI-OWNERS'
TITLE='保存callbackとresourceを固定JPの描画owner・構造体境界へ結合'
SELF='scripts/pr16_ring_ui_owners.py'
TEST='tests/test_pr16_ring_ui_owners.py'
WORKFLOW='.github/workflows/pr16-ring-ui-owners.yml'
PRIOR='content/modernization/pr16_ring_resource_contracts.json'
REPORT='content/modernization/pr16_ring_ui_owners.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=24
EXTRA_CODE=()
SOURCES=('state/source-lock.json','scripts/pr16_ring_resource_tail.py',
    'content/modernization/pr16_ring_resource_tail.json')
PINS={'cfru':('kapibarasan000/CFRU-JP','e24a16fe39e27ae162faf5b78596d1f3df18489d'),
      'pokefirered':('pret/pokefirered','c75f352304d529f6ba92d4f74b9cf8b5c3810788')}
SOURCE_PATHS={'cfru':('BPRJ.ld','include/text.h','include/window.h'),
              'pokefirered':('src/text.c','src/window.c')}
EXPECTED={'AddTextPrinter':0x08002cf1,'RenderFont':0x08002e4d,
          'CopyWindowToVram':0x08003eed,'gWindows':0x02020430}
ROOT_NAMES=('SetFontsPointer','DeactivateAllTextPrinters','RunTextPrinters',
    'SetDefaultFontsPointer','InitWindows','AddWindow','RemoveWindow','FreeAllWindowBuffers')
TERMS=('gFonts','gTextPrinters','sTempTextPrinter','sFontInfos','FontInfo','TextPrinter',
       'NUM_TEXT_PRINTERS','WINDOWS_MAX','gWindows','WindowTemplate','struct Window',*ROOT_NAMES)
NO_REPEAT=('固定source-lockのJP symbolと描画owner/ヘッダABI照合を再利用。'
    '保存32byte text slotとCFRU36byte TextPrinterの差を保持し、ヘッダだけでlive allocationやRing取得を受入しない。'
    '先行resource1752契約・2970命令採取・BP/nativeを単独再実行しない。')


def need(ok,text):
    if not ok:raise ValueError(text)


def identity(raw):return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def strip_comments(text):
    need(type(text)is str,'source text')
    return re.sub(r'/\*.*?\*/|//[^\n]*',lambda m:'\n'*m[0].count('\n'),text,flags=re.S)


def symbols(text):
    clean=strip_comments(text);out={}
    pattern=r'^\s*([A-Za-z_]\w*)\s*=\s*(0x[0-9A-Fa-f]+)\s*(?:\|\s*(1))?\s*;\s*$'
    for m in re.finditer(pattern,clean,re.M):
        name=m[1];value=int(m[2],16)|int(m[3]or'0')
        need(value<=0xffffffff,'symbol u32')
        need(name not in out or out[name]==value,'symbol競合 '+name)
        out[name]=value
    return out


def checked_source(payload):
    need(type(payload)is dict and payload.get('encoding')=='base64','source encoding')
    need(type(payload.get('sha'))is str and re.fullmatch('[0-9a-f]{40}',payload['sha']),'source blob SHA')
    encoded=payload.get('content');need(type(encoded)is str and len(encoded)<1400000,'source size')
    try:raw=base64.b64decode(''.join(encoded.split()),validate=True)
    except Exception as exc:raise ValueError('source base64')from exc
    need(0<len(raw)<=1000000 and payload.get('size')==len(raw),'source byte size')
    sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    need(sha==payload['sha'],'source blob不一致')
    text=raw.decode('utf-8');need('\0'not in text,'source NUL')
    return text,{'git_blob':sha,**identity(raw)}


def checked_pins(lock):
    need(type(lock)is dict and type(lock.get('sources'))is list,'source lock')
    result={}
    for name,(repo,commit)in PINS.items():
        rows=[r for r in lock['sources']if r.get('name')==name]
        need(len(rows)==1,'固定source一意性 '+name);row=rows[0]
        need(row.get('repository')=='https://github.com/'+repo+'.git','source repository')
        need(all(row.get(k)==commit for k in ('configured_commit','actual_commit','resolved_commit'))
             and row.get('configured_commit_verified')is True,'固定commit不一致')
        result[name]={'repository':repo,'commit':commit}
    return result


def source_path(name,path):
    need(name in SOURCE_PATHS and path in SOURCE_PATHS[name],'source allowlist')
    need(not PurePosixPath(path).is_absolute()and '..'not in PurePosixPath(path).parts,'source path')
    repo,commit=PINS[name]
    return 'repos/'+repo+'/contents/'+path+'?ref='+commit


def excerpts(text):
    lines=text.splitlines();hits=[i for i,line in enumerate(lines)if any(t in line for t in TERMS)]
    need(len(hits)<=600,'source hits上限')
    return [{'line':i+1,'text':lines[i]}for i in hits]


def abi_layout(text,window):
    # 32bit pointerを明示し、hostの64bit pointer sizeへ依存しない。
    need('#define NUM_TEXT_PRINTERS 32'in strip_comments(text),'printer count定義')
    need('u8 minLetterSpacing;'in text and 'u8 japanese;'in text,'CFRU trailing fields')
    need('struct WindowTemplate'in window and 'struct Window'in window,'window定義')
    class Printer(ctypes.LittleEndianStructure):
        _fields_=[('template',ctypes.c_uint32*4),('callback',ctypes.c_uint32),
                  ('sub',ctypes.c_uint8*7),('active',ctypes.c_uint8),('state',ctypes.c_uint8),
                  ('speed',ctypes.c_uint8),('delay',ctypes.c_uint8),('scroll',ctypes.c_uint8),
                  ('minimum',ctypes.c_uint8),('japanese',ctypes.c_uint8)]
    need(Printer.active.offset==27 and Printer.minimum.offset==32 and ctypes.sizeof(Printer)==36,'明示ABI model')
    return {'pointer_bits':32,'header_printer_count':32,'header_printer_bytes':36,
        'saved_candidate_slot_bytes':32,'header_extra_offsets':[32,33],
        'header_stride_matches_candidate':False,'header_is_candidate_allocation_proof':False}


def join(nodes,table):
    need(type(nodes)is list and len(nodes)==2970,'保存2970命令')
    known={n['address']:n for n in nodes};need(len(known)==len(nodes),'重複node')
    for name,value in EXPECTED.items():need(table.get(name)==value,'JP symbol境界 '+name)
    checks=((0x08002cf0,'f0b5'),(0x08002e4c,'10b5'),(0x08003eec,'70b5'),
            (0x08002d5e,'4901'),(0x08002db6,'4901'),(0x08002e58,'4018'),(0x08002e5a,'8000'))
    for at,raw in checks:need(known.get(at,{}).get('hex')==raw,'保存owner命令差分')
    literals=((0x08002cfa,0x03003dd0),(0x08002e52,0x03003dd0),
              (0x08002d5a,0x02020030),(0x08003efa,0x02020430))
    for at,value in literals:need(known.get(at,{}).get('literal_value')==value,'保存global差分')
    roots=[]
    for name in ROOT_NAMES:
        target=table.get(name)
        if target is not None:
            need(type(target)is int and target&1 and 0x08000000<=target<0x0a000000,'JP owner root')
            roots.append({'symbol':name,'entry':target,'already_saved':(target&~1)in known})
    return {'jp_symbol_bindings':dict(EXPECTED),'saved_sites':dict(checks),
        'callback_global':0x03003dd0,'callback_record_stride':12,'callback_selector_offset':5,
        'output_pool':0x02020030,'output_stride':32,'resource_pool':0x02020430,'resource_stride':12,
        'next_named_roots':roots,'missing_named_roots':[n for n in ROOT_NAMES if n not in table],
        'symbol_name_is_execution_proof':False,'source_header_is_live_allocation_proof':False}


def analyze(previous,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_resource_tail as tail
    pins=checked_pins(s.load('state/source-lock.json'));snapshots={};provenance={}
    for name in SOURCE_PATHS:
        for path in SOURCE_PATHS[name]:
            text,receipt=checked_source(json.loads(s.cmd('gh','api',source_path(name,path))))
            key=name+'/'+path;snapshots[key]=text
            provenance[key]={**pins[name],**receipt,'path':path,'relevant_lines':excerpts(text)}
    (out/'source-snapshots.json').write_bytes(s.stable(snapshots))
    (out/'source-provenance.json').write_bytes(s.stable(provenance))
    nodes,_,_=tail.saved_inputs();nodes=[*nodes,*s.load(tail.REPORT)['analysis']['new_nodes']]
    result=join(nodes,symbols(snapshots['cfru/BPRJ.ld']))
    result.update({'classification':'PINNED_JP_UI_OWNER_BINDINGS_NOT_LIVE_ALLOCATION_OR_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'source_provenance':provenance,
        'header_abi':abi_layout(snapshots['cfru/include/text.h'],snapshots['cfru/include/window.h']),
        'saved_node_count':len(nodes),'unbound_runtime_data':copy.deepcopy(previous['analysis']['unbound_runtime_data']),
        'all_callers_resolved':False,'all_live_frames_proven':False,'all_runtime_owners_excluded':False,
        'all_dispatch_returns_proven':False,'all_live_slot_bounds_proven':False,
        'caller_pointer_size_limit_proven':False,'actual_callback_table_observed':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':0,'new_byte_samples':0,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,
        'preconditions':['JP ldは固定sourceのbinding。候補命令の名前対応であり全実装一致・live到達を意味しない。',
            'pretは別地域reference。source配列長をJP candidateの実allocationへ転記しない。',
            '32byte候補slotへ36byteヘッダstrideを適用しない。次はJP initializerの保存命令・実tableの限定照合。']})
    (out/'source-snapshots.json').write_bytes(s.stable(snapshots))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':nodes}))
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(result):
    return ('保存callback/resourceを固定JPのAddTextPrinter・RenderFont・CopyWindowToVram・gWindowsへ結合。'
        '候補32byte text slotとCFRUヘッダ36byteのABI差を保持。live allocationとRing取得は未受入。',
        '次は今回特定したJP initializer/RunTextPrinters/InitWindowsの未読rootだけを有限採取し、'
        'gFonts実table・32byte出力slot・12byte window配列の初期化/到達境界を結合する。'
        'US referenceや36byteヘッダをJPの実allocationへ昇格しない。'
        '既読2970命令・resource1752契約・BP/nativeは再実行しない。Ring正規取得/装備実戦/保存・policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
