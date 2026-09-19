#!/usr/bin/env python3
"""保存graphと固定referenceからstory入口の未読callerを有限に限定する。"""
from __future__ import annotations
import copy
import functools
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile
import pr16_ring_followup_v2 as s
import pr16_ring_text_export_recovery as export
import pr16_ring_ui_owners as owners

BASE='843582c76c8b0b9423afc6202b9a2553542b03d9'
SLUG='pr16-ring-story-caller-frontier'
TASK='PR-P08-7-RING-STORY-CALLER-FRONTIER'
TITLE='保存graphと固定sourceからstory初期化callerとscript命令表の未読接続を限定'
SELF='scripts/pr16_ring_story_caller_frontier.py'
TEST='tests/test_pr16_ring_story_caller_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-story-caller-frontier.yml'
PRIOR='content/modernization/pr16_ring_bootstrap_lifecycle_contracts.json'
REPORT='content/modernization/pr16_ring_story_caller_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=37
EXTRA_CODE=()
SOURCES=(owners.SELF,export.SELF,s.SELF,'scripts/pr16_ring_message_task_frontier.py','state/source-lock.json',
    'content/modernization/pr16_ring_ui_owners.json')
NETWORK='GitHub connector/Actionsとsource-lock固定pretの限定7source。既存JP symbol/8628命令は保存原本を再利用。source-lock変更/ROM復元/native再実行0。'
NO_REPEAT='保存8628命令の3入口inbound照合と固定reference限定caller索引を再利用。未保存caller不存在やJP candidate実到達とは読まない。次は索引の未読caller/tableのcandidate byteを限定し、bootstrap/text/BP/nativeを単独再実行しない。'
TARGETS={'SetDefaultFontsPointer':0x080f8a29,'DeactivateAllTextPrinters':0x08002c29,'ScrCmd_message':0x0806b0cd}
REFERENCE_PATHS=('src/overworld.c','src/scrcmd.c','src/script.c','src/text_window.c',
    'src/new_menu_helpers.c','src/field_message_box.c','data/script_cmd_table.inc')
BOOT_ARTIFACT=10534283048
BOOT_SHA='c042ed78e09ddc0b5a5518800fb75008ea01d32bbc5bdc49aa8604dd1bb87ce9'
CONTEXT_SHA='c72a47cc475f5f5a73381c7efce22ddb847710f8a01a4ee4ffd088f612a12f8d'
JP_ARTIFACT=10486748720
JP_SHA='0d13cbceeef226acfb5ff9907dc408e8fce1db2e0f91a87a66b5405328b5b6a0'
need=s.need


def artifact(number,digest,name):
    """固定ZIPのみ。既存cacheも毎回hashを確認し、archive pathを実行しない。"""
    path=s.ROOT/'.local'/SLUG/name
    if not path.exists():
        raw=subprocess.check_output(['gh','api',f'repos/{s.REPO}/actions/artifacts/{number}/zip'])
        need(hashlib.sha256(raw).hexdigest()==digest,'artifact hash')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    raw=path.read_bytes();need(hashlib.sha256(raw).hexdigest()==digest,'cache hash')
    return zipfile.ZipFile(io.BytesIO(raw))


@functools.lru_cache(maxsize=1)
def context():
    with artifact(BOOT_ARTIFACT,BOOT_SHA,'bootstrap.zip') as z:
        names=z.namelist();need(len(names)==len(set(names)),'archive重複')
        manifest=json.loads(z.read('export/manifest.json'));row=manifest['files']['saved-context.json']
        chunks=[]
        for index,part in enumerate(row['parts']):
            name=part['path'];need(re.fullmatch(r'file-\d{4}-part-\d{4}\.json',name),'chunk path')
            raw=z.read('export/'+name);need(s.identity(raw)==part['identity'],'chunk identity')
            v=json.loads(raw)
            need(v['file']=='saved-context.json' and v['index']==index and v['count']==len(row['parts']),'chunk順序')
            chunks.append(v['text'])
        raw=''.join(chunks).encode('utf-8')
        need(s.identity(raw)==row['identity'] and hashlib.sha256(raw).hexdigest()==CONTEXT_SHA,'context identity')
        return json.loads(raw)


def saved_inbound(nodes,targets=TARGETS):
    need(type(nodes)is list and type(targets)is dict and targets,'graph引数')
    by={};occupied=set()
    for n in nodes:
        at,size=n['address'],n['size'];raw=bytes.fromhex(n['hex'])
        need(type(at)is int and not at&1 and size in(2,4) and len(raw)==size,'node境界')
        cells=set(range(at,at+size));need(not cells&occupied and at not in by,'node重複')
        by[at]=n;occupied|=cells
    result={}
    for name,entry in targets.items():
        need(type(entry)is int and entry&1 and (entry&~1)in by,'入口欠落/Thumb')
        inbound=[]
        for n in nodes:
            if n.get('kind')in('call','jump','conditional') and n.get('target',0)&~1==entry&~1:
                inbound.append({'site':n['address'],'kind':n['kind'],'target':entry,'hex':n['hex']})
            if n.get('literal_value')==entry:
                inbound.append({'site':n['address'],'kind':'literal_reference_not_executed_call','target':entry,'literal_address':n['literal_address']})
        result[name]={'entry':entry,'saved_inbound':inbound,'all_callers_excluded':False}
    return result


def mask_c(text):
    """commentと文字列を同じ長さの空白へ。source lineと括弧の位置を保持。"""
    need(type(text)is str and '\0'not in text,'C text')
    pattern=r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    return re.sub(pattern,lambda m:re.sub(r'[^\n]',' ',m[0]),text,flags=re.S)


def definitions(text):
    clean=mask_c(text);out=[]
    pattern=r'(?m)^[ \t]*([A-Za-z_][^\n;{}()]*?)\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{'
    for m in re.finditer(pattern,clean):
        # else if / else while は型名+関数に似るが、既読関数の内部に限る。
        if out and m.start()<out[-1]['end']:
            need(m[2] in ('if','while','for','switch'), '未対応の入れ子関数定義')
            continue
        need(m[2] not in ('if','while','for','switch'),'top-level制御構文')
        start=m.end()-1;depth=1;end=start+1
        while end<len(clean) and depth:
            depth+=(clean[end]=='{')-(clean[end]=='}');end+=1
        need(depth==0,'閉じていない関数')
        need(not out or m.start()>=out[-1]['end'],'重複関数定義')
        body=clean[start+1:end-1]
        calls=[{'symbol':v[1],'line':clean.count('\n',0,start+1+v.start())+1}
               for v in re.finditer(r'\b([A-Za-z_]\w*)\s*\(',body)
               if v[1] not in ('if','for','while','switch','sizeof','return')]
        out.append({'name':m[2],'start':m.start(),'end':end,
                    'line':clean.count('\n',0,m.start())+1,'calls':calls})
    return out


def source_callers(snapshots,targets=tuple(TARGETS),depth=4):
    need(type(depth)is int and 1<=depth<=6,'caller深さ')
    defs=[]
    for path,text in snapshots.items():
        if path.endswith('.c'):
            defs.extend(dict(d,path=path)for d in definitions(text))
    wanted=set(targets);seen=set();rows=[];waves=[]
    for level in range(depth):
        next_names=set();batch=[]
        for d in defs:
            hits=[v for v in d['calls']if v['symbol']in wanted]
            for hit in hits:
                identity=(d['path'],d['name'],hit['line'],hit['symbol'])
                if identity in seen:continue
                seen.add(identity);next_names.add(d['name'])
                batch.append({'path':d['path'],'caller':d['name'],'definition_line':d['line'],
                    'site_line':hit['line'],'callee':hit['symbol'],'depth':level+1,
                    'reference_only_not_candidate_binding':True})
        rows.extend(batch);waves.append({'depth':level+1,'edges':len(batch)})
        wanted=next_names
        if not wanted:break
    return {'edges':rows,'waves':waves,'parsed_function_count':len(defs),
        'bounded_paths':list(snapshots),'maximum_depth':depth,'all_reference_callers_enumerated':False}


def command_table(text):
    """固定referenceの連続.4byte表。未知directive/空表を拒否する。"""
    clean=re.sub(r'@[^\n]*','',text)
    need(clean.count('gScriptCmdTable::')==1 and clean.count('gScriptCmdTableEnd::')==1,'command表label')
    body=clean.split('gScriptCmdTable::',1)[1].split('gScriptCmdTableEnd::',1)[0]
    names=[]
    for line in body.splitlines():
        if not line.strip():continue
        m=re.fullmatch(r'\s*\.4byte\s+(ScrCmd_[A-Za-z0-9_]+)\s*',line)
        need(m is not None,'未知command表directive');names.append(m[1])
    need(0<len(names)<=256,'command表size')
    return names


def reference_path(path):
    need(path in REFERENCE_PATHS,'reference allowlist')
    repo,sha=owners.PINS['pokefirered']
    return f'repos/{repo}/contents/{path}?ref={sha}'


def analyze(previous,out):
    owners.checked_pins(s.load('state/source-lock.json'))
    c=context();a=previous['analysis']
    need(c['bootstrap_lifecycle']=={k:v for k,v in a.items() if k!='export_manifest'}
        and a['successful_lifecycles']==12 and a['contract_cases']==14,'bootstrap原本')
    need(len(c['nodes'])==8628 and a['normal_story_initializer_reachability_proven']is False,'到達境界')
    inbound=saved_inbound(c['nodes'])
    need(all(not row['saved_inbound']for row in inbound.values()),'未読caller境界が変化')
    with artifact(JP_ARTIFACT,JP_SHA,'jp-source.zip') as z:
        snapshots,provenance=owners.verify_snapshots(json.loads(z.read('source-snapshots.json')),
            json.loads(z.read('source-provenance.json')))
    jp=owners.symbols(snapshots['cfru/BPRJ.ld'])
    corrected=json.loads(subprocess.check_output(['gh','api',f'repos/{s.REPO}/actions/runs/35315698648']))
    need(corrected['status']=='completed' and corrected['conclusion']=='cancelled','旧WIP中止の原結論')
    fresh={};sources={}
    for path in REFERENCE_PATHS:
        payload=json.loads(subprocess.check_output(['gh','api',reference_path(path)]))
        text,ident=owners.checked_source(payload);fresh[path]=text
        sources[path]=dict(ident,repository=owners.PINS['pokefirered'][0],commit=owners.PINS['pokefirered'][1])
    (out/'reference-sources.json').write_bytes(s.stable(fresh))
    (out/'reference-provenance.json').write_bytes(s.stable(sources))
    calls=source_callers(fresh);table=command_table(fresh['data/script_cmd_table.inc'])
    need(table[0x67]=='ScrCmd_message' and table[0x66]=='ScrCmd_waitmessage','reference message opcode')
    relevant=set(TARGETS)|{r['caller']for r in calls['edges']}|{'InitScriptContext','SetupBytecodeScript','RunScriptCommand','gScriptCmdTable','ScriptContext1_RunScript'}
    bindings={name:jp.get(name)for name in sorted(relevant)}
    bounded=[dict(r,jp_symbol_entry=jp.get(r['caller']),candidate_byte_binding_proven=False)for r in calls['edges']]
    result={'classification':'BOUNDED_STORY_CALLER_REFERENCE_INDEX_NOT_CANDIDATE_REACHABILITY',
        'candidate':dict(s.CANDIDATE),'saved_node_count':len(c['nodes']),'saved_inbound':inbound,
        'reference_callers':dict(calls,edges=bounded),'reference_script_table':{'count':len(table),'message_opcode':0x67,'message_symbol':table[0x67],'waitmessage_opcode':0x66,'candidate_table_address':None},
        'jp_symbol_candidates':bindings,'source_provenance':sources,
        'saved_jp_symbol_provenance':provenance['cfru/BPRJ.ld'],
        'remaining_initial_input_assumptions':copy.deepcopy(a['remaining_initial_input_assumptions']),
        'bootstrap_origin':{'run_id':35313824566,'artifact_id':BOOT_ARTIFACT,'zip_sha256':BOOT_SHA,'context_sha256':CONTEXT_SHA},
        'new_upstream_source_files':len(fresh),'accepted_upstream_sources_refetched':0,
        'failed_original_attempt':{'run_id':35315330711,'job_id':105505636383,
            'head':'71f5d89a5a2b5ccd9a4b2b18a1d8c0b25bfb8471','conclusion':'failure',
            'artifact_id':10535110418,'zip_sha256':'0dd7e1d6bf388a7d7b507ca317972238e2bc16087312d98903f2e963f3dd2faf',
            'failure_boundary':'制御構文と入れ子関数候補の区別不足・解析時にfail closed',
            'tests_passed':31,'record_commit_created':False},
        'cancelled_parser_attempt':{'run_id':35315698648,'head':corrected['head_sha'],
            'conclusion':corrected['conclusion'],'cause':'長い空白の宣言で字句正規表現が過剰backtracking。37testsへ追加して置換。'},
        'candidate_reconstructions':0,'rom_changes':0,'new_window_bytes':0,'new_node_count':0,
        'new_emulator_processes':0,'saved_nodes_redecoded':0,'accepted_standalone_contracts_replayed':0,'accepted_native_cases_replayed':0,
        'normal_story_observed':False,'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'7固定referenceファイル/深さ4の字句call索引。JP symbolの別名/欠落は未解決。実candidate caller/table byte照合と通常story実行は次工程。'}
    from pr16_ring_message_task_frontier import source_export
    files=source_export((SELF,TEST,*SOURCES))
    files['saved-context.json']=s.stable(dict(c,story_caller_frontier=result))
    files['reference-sources.json']=s.stable(fresh)
    files['jp-symbols.json']=s.stable(jp)
    export.bundle(files,out/'export')
    result['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(r):
    count=len(r['reference_callers']['edges'])
    return (f'保存8628命令では初期化080F8A29/reset08002C29/script0806B0CDへのinboundなし。固定reference7ファイルから深さ4のcaller{count}辺とmessage opcode67を索引化。JP symbol候補/別地域reference/実candidate到達を区別。旧初期化・text/native再実行0。',
        '保存caller索引のInitStandardTextBoxWindows等とscript command table/RunScriptCommandの未読candidate接続を限定採取・照合する。通常story開始から初期化/command dispatchへ到達したとは未主張。config/global/windowの初期入力仮定を残し、通常Ring取得/保存とpolicy/Circus/P08は未受入。保存bootstrap/text/BP/nativeは単独再実行しない。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可')
    sys.modules['pr16_ring_story_caller_frontier']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
