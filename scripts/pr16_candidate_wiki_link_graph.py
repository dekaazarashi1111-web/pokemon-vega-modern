#!/usr/bin/env python3
"""保存link名を入口に、現候補Thumb-1の有界構造graphを読む。実行/全callee同定とは別。"""
from __future__ import annotations
from collections import Counter
import sys
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import Inputs, Rom, BASE, STATE, digest, need, stable
SNAPSHOT='content/modernization/pr16_candidate_wiki_link_sources.json'
SELF='scripts/pr16_candidate_wiki_link_graph.py'
DEFERRED='DEFERRED_AUDIT'


def signed(value: int, bits: int) -> int:
    return value-(1<<bits) if value & (1<<(bits-1)) else value


def instruction(rom: Rom, pc: int) -> dict:
    need(type(pc) is int and pc%2==0,'Thumb命令境界不正')
    h=rom.u16(pc); kind='FALLTHROUGH'; edges=[pc+2]; detail={}; size=2
    if h & 0xF800 == 0xF000:
        low=rom.u16(pc+2)
        if low & 0xF800 != 0xF800:
            kind='UNSUPPORTED_LONG_BRANCH';edges=[]
        else:
            size=4;kind='DIRECT_BL';edges=[pc+4]
            detail['call_target']=pc+4+(signed(h&2047,11)<<12)+((low&2047)<<1)
    elif h & 0xF800 == 0xE000:
        kind='DIRECT_B';edges=[pc+4+(signed(h&2047,11)<<1)]
    elif h & 0xF000 == 0xD000:
        condition=(h>>8)&15
        kind='CONDITIONAL_B' if condition<14 else 'TRAP_OR_UNDEFINED'
        edges=[pc+2,pc+4+(signed(h&255,8)<<1)] if condition<14 else []
        detail['condition_code']=condition
    elif h & 0xFC00 == 0x4400:
        op=(h>>8)&3;dest=(h&7)|((h>>4)&8);src=(h>>3)&15
        if op==3 or (op in (0,2) and dest==15):
            kind='INDIRECT_PC_TRANSFER';edges=[];detail['register']=src
    elif h & 0xFE00 == 0xBC00 and h & 256:
        kind='POP_PC_RETURN_OR_INDIRECT';edges=[]
    elif h & 0xF800 == 0x4800:
        literal=((pc+4)&~3)+4*(h&255)
        value=rom.u32(literal);kind='PC_RELATIVE_LITERAL_LOAD';detail['literal_site']=literal
        if BASE <= value < BASE+len(rom.raw):detail['rom_pointer_value']=value
    elif (h < 0x4400 or 0x5000<=h<0xB000 or h & 0xFF00 == 0xB000
          or h & 0xFE00 in (0xB400,0xBC00) or 0xC000<=h<0xD000 and h&255):
        pass
    else:
        kind='UNSUPPORTED_ENCODING';edges=[]
    return {'address':pc,'kind':kind,'size':size,'encoding_sha256':digest(rom.read(pc,size)),
            'successors':sorted(set(edges)),**detail}


def structural_graph(rom: Rom, entry: int, start: int, end: int, limit: int=2048) -> dict:
    need(type(limit) is int and 0<limit<=8192,'graph上限不正')
    need(start<=entry<end and start%2==entry%2==0 and end<=BASE+len(rom.raw),'graph入口/範囲不正')
    pending=[entry];visited={};outside=set();overlap=set()
    while pending and len(visited)<limit:
        pc=pending.pop()
        if pc in visited:continue
        if not start<=pc<=end-2:
            outside.add(pc);continue
        try:
            row=instruction(rom,pc)
            need(pc+row['size']<=end,'命令がgraph範囲を超過')
        except ValueError:
            row={'address':pc,'kind':'TRUNCATED_INSTRUCTION_OR_LITERAL','successors':[],'size':2}
        visited[pc]=row
        pending.extend(reversed(row['successors']))
    for pc,row in visited.items():
        if row['size']==4 and pc+2 in visited:overlap.add(pc+2)
    return {'entry':entry,'nodes':[visited[p] for p in sorted(visited)],'node_count':len(visited),
        'direct_calls':[{'site':r['address'],'target':r['call_target']} for r in sorted(visited.values(),key=lambda r:r['address']) if r['kind']=='DIRECT_BL'],
        'outside_branches':sorted(outside),'instruction_overlap_sites':sorted(overlap),'limit_reached':bool(pending),
        'terminal_kinds':dict(sorted(Counter(r['kind'] for r in visited.values() if not r['successors']).items())),
        'conditional_paths_are_overapproximation':True,'indirect_edges_resolved':False,
        'full_function_extent_proven':False,'native_acceptance':DEFERRED}


def validate_snapshot(value: dict, candidate: dict, meta_raw: bytes) -> None:
    need(value['candidate']==candidate,'link candidate不一致')
    need(len(meta_raw)==value['metadata']['size'] and digest(meta_raw)==value['metadata']['sha256'],'保存link metadata変更')
    need(len({r['symbol'] for r in value['symbol_windows']})==len(value['symbol_windows']),'link symbol曖昧')
    need({r['symbol'] for r in value['symbol_windows']}=={'HandleInputChooseMove','VegaBattlePolicyCanZ','VegaBattlePolicyMarkZ'},'入口symbol契約変更')
    need(not value['available_link_paths'] and not value['offset_bindings'],'新規link表あり。未保存扱いを継続しない')
    need(all(r['symbol_extent']=='NOT_PROVEN_WITHOUT_ELF_SIZE' for r in value['symbol_windows']),'窓を関数全体と誤認')


def enrich(model: dict, inputs: Inputs, raw: bytes) -> dict:
    inputs.raw(SELF);value=inputs.json(SNAPSHOT)
    validate_snapshot(value,model['candidate'],inputs.raw(value['metadata']['path']))
    rom=Rom(raw); start=BASE+value['payload']['start'];end=start+value['payload']['size'];graphs=[]
    names={int(r['address'],16):r['symbol'] for r in value['symbol_windows']}
    for seed in value['symbol_windows']:
        entry=int(seed['address'],16)
        need(digest(rom.read(entry,seed['window_size']))==seed['candidate_window_sha256'],'candidate入口window変更')
        graph=structural_graph(rom,entry,start,end)
        for call in graph['direct_calls']:
            call['target_symbol_from_saved_metadata']=names.get(call['target'])
        graph.update(seed_symbol=seed['symbol'],seed_scope='SAVED_STAGE06_SYMBOL_AT_CURRENT_CANDIDATE_ADDRESS',
                     source_equivalence_not_proven=True,seed_window=seed)
        graphs.append(graph)
    missing=value['missing_symbols']
    result={'schema_version':1,'candidate':model['candidate'],'graphs':graphs,'saved_link_input':value,
        'summary':{'link_graph_seeds':len(graphs),'link_graph_nodes':sum(r['node_count'] for r in graphs),
            'link_graph_direct_bl_sites':sum(len(r['direct_calls']) for r in graphs),
            'link_graph_overlap_sites':sum(len(r['instruction_overlap_sites']) for r in graphs),
            'link_graph_limited_seeds':sum(r['limit_reached'] for r in graphs),'missing_named_link_symbols':len(missing)},
        'new_native_runs':0,'rom_changes':0,'complete_z_callgraph':False,
        'limits_ja':'保存metadataの3入口から到達し得るThumb-1命令を有界に追う。条件分岐は両側、BL先関数へは入らず、BX/POP PC/PC書換/未対応命令で止まる。source同一性・全関数範囲・実行済みは主張しない。'}
    model['link_graph_audit']=result;model['followup_audit']['summary'].update(result['summary'])
    todo=model['followup_audit']['remaining_work_ja'];targets=[i for i,s in enumerate(todo) if s.startswith('汎用Zの実行時split規則')]
    need(len(targets)==1,'Z caller残件anchor不一致')
    todo[targets[0]]='汎用Zのsplit/候補表に加え保存metadataの3入口からThumb-1構造graphを抽出済み。残りはCanUseZMove/GetTypeBasedZMove/CalcMoveSplitの名前付きcallee結合・間接辺。既存offsets.ini/linked.oの固定hashはlink_graph_auditに記録。再build/nativeなしに名前を推測しない。'
    model['source_bindings'].update({k:v for k,v in inputs.bindings.items() if k!=STATE})
    return model


def append_pages(files: dict[str,bytes],model: dict) -> None:
    from pr16_candidate_wiki_render import jsonblock,table
    value=model['link_graph_audit']
    text='# Z関連入口のcompiled構造graph\n\n[Wiki入口](README.md) / [Z split監査](RUNTIME_Z_AUDIT.md)\n\n'
    text+=value['limits_ja']+'\n\n'+jsonblock(value['summary'])
    text+='\n## 保存metadataで名前が確認できた入口\n\n'+table(['入口名','現候補address','到達候補命令','直接BL','停止理由'],[(g['seed_symbol'],hex(g['entry']),g['node_count'],len(g['direct_calls']),g['terminal_kinds']) for g in value['graphs']])
    text+='\n## 未保存link表\n\n全offsetsは13,131 symbols、SHA-256 `f9851fb5eea759573d1e4e0b923e69c34c85ddb171fb03321f5b7ce380870523`。linked.oは5,733,212 bytes、SHA-256 `52bbd57a7d2649164c4706ee45dc17ef1f8357862d8dbd79bdcd439c2b0a36fb`。今回調べた保存先に実体なし。再コンパイルや近傍prologueからの命名はしていません。\n\n'
    text+='[各命令・BL先・入力hash・未解決辺](data/link_graph_audit.json)\n'
    files['LINK_GRAPH_AUDIT.md']=text.encode();files['data/link_graph_audit.json']=stable(value)
    for name in ('README.md','Z_MOVE_INDEX.md','RUNTIME_LIMITATIONS.md','CODEX_INDEX.md'):
        files[name]+='\n[Z関連入口のcompiled構造graphと未解決callee](LINK_GRAPH_AUDIT.md)\n'.encode()
