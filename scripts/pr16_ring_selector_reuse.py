#!/usr/bin/env python3
"""既存external1/2/3保存graphを再利用結合し、今回2工程の原Actions/ZIP/commitを照合。"""
from __future__ import annotations
import copy
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

BASE='67cad0bc29c3614993d091c0687d36ee6da4c3a8'
SLUG='pr16-ring-selector-reuse'
TASK='PR-P08-7-RING-SELECTOR-REUSE'
TITLE='既存external3根の保存graph再利用と2工程の成功原本を結合'
SELF='scripts/pr16_ring_selector_reuse.py'
TEST='tests/test_pr16_ring_selector_reuse.py'
WORKFLOW='.github/workflows/pr16-ring-selector-reuse.yml'
PRIOR='content/modernization/pr16_ring_dispatch_contracts.json'
REPORT='content/modernization/pr16_ring_selector_reuse.json'
KEY='latest_ring_diagnostic'
SOURCES=()
EXTRA_CODE=()
MIN_TESTS=30
NAMES=('external1_abi','external1_cont_abi','external1_exit_abi','external2_abi',
       'external3_abi','external3_body_abi','external3_tail_abi')
OLD_HASHES=dict(zip(NAMES,(
    '6b85751600d2ac75f64bd24dc725bbd1b197ca4c99203faa1ee06c74f44be3c4',
    'fe9fa33b50dece21cac9f2c9f04b5bd37916947d79a4443894198166d7d71be4',
    '1ee79e8e8305d50af84104dd9984502df656a5c3632c22efa81008ed28baa7c6',
    '10171fb0872ab4ec7390ba828178c109ba4b0391c93d6f90a87785f49a46880c',
    'abb56976a0d74faeabbf3b80b63b58ec58b697ce932193c4593e5c7eb9943acc',
    'f2677bcd192914fc1f629811d48c470f570361686b96e1ee383be561b7618b0d',
    'ffe7d250077f69858d56d331d567ec073484b761e9fa25c952b0b4e7e4d96664')))
REUSED=(0x0806dd1d,0x08113889,0x081138f9)
RESOURCE=(0x080011e5,0x08001299,0x080014f1,0x0800273d,0x080027ad,0x08002899,0x080028ed,0x08002901)
REGIONS=((0x0806dd1c,0x0806dd56),(0x08113888,0x08113966))
BYTE_RE=re.compile(r'content/modernization/pr16_ring_external[123](?:_(?:cont|exit|body|tail))?_bytes\.json\Z')
CANDIDATE={'size':33554432,'sha256':'ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b','crc32':'3EB17B36'}
STAGES=(
 {'slug':'pr16_ring_dispatch_frontier','run':35189858767,'job':105099821934,'artifact':10483757804,
  'source':'f25707e6a655a3beb41882a10d124f2171d75799','commit':'ed8d6e9e8a0284a747d1d6769185d230e0d10222',
  'digest':'35de982e85b5275855a58e0cb2e6c22caaff074d79f7088e3ab2d14c0837ef51','tests':23},
 {'slug':'pr16_ring_dispatch_contracts','run':35190870442,'job':105102929360,'artifact':10483749352,
  'source':'9e14bfb6ec932f1411fe072beb5aec9385db59b1','commit':BASE,
  'digest':'ff1eee1da8a3bbc3fdf77deafdf69799d93a2f9334860e703e346e6ea9eda673','tests':38})
NO_REPEAT=('保存external1/2/3の7byte graphを現在の2330命令へ再利用結合した。'
    '今回2工程の成功Actions/原ZIP/保存commitを照合済み。採取・旧ABI・VarGet全u16/1337帰還・BP/nativeを単独再実行しない。'
    '既知nodeへの再結合はselector callerの全帰還や実allocation/Ring取得の証明ではない。')


def need(ok,text):
    if not ok:raise ValueError(text)


def identity(raw):return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def strict(raw):
    def pairs(items):
        out={}
        for k,v in items:need(k not in out,'JSON重複key');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:need(False,'JSON非有限値'))


def report_checked(raw,expected):
    need(identity(raw)['sha256']==expected,'保存report hash差分')
    value=strict(raw);need(value['schema_version']==1 and value['analysis']['candidate']==CANDIDATE,'保存candidate/schema差分')
    t=value['focused_tests'];need(t['successful']is True and type(t['tests_run'])is int and t['tests_run']>0
        and all(type(t[k])is int and t[k]==0 for k in ('failures','errors','skips')),'保存tests未完')
    for key in ('ring_acquisition_accepted','release_ready'):need(value['analysis'][key]is False,'保存受入境界 '+key)
    return value


def byte_paths(report):
    result={p:v for p,v in report['source_bindings'].items()if BYTE_RE.fullmatch(p)}
    need(result,'external byte source bindingなし');return result


def merge_nodes(cached,graphs):
    need(type(cached)is list and type(graphs)is dict and graphs,'graph入力')
    known={};occupied={};added=[];provenance={}
    def insert(n,owner):
        need(type(n)is dict and {'address','size','hex','kind'}<=n.keys(),'node形式')
        at,size=n['address'],n['size'];raw=bytes.fromhex(n['hex'])
        need(type(at)is int and at%2==0 and type(size)is int and size in (2,4)and len(raw)==size,'node整列/幅')
        if owner!='cached':need(any(lo<=at and at+size<=hi for lo,hi in REGIONS),'旧external範囲逸脱')
        if at in known:
            need(n==known[at],'重複node矛盾');provenance.setdefault(str(at),[]).append(owner);return
        need(not any(p in occupied for p in range(at,at+size)),'命令operand重複')
        known[at]=copy.deepcopy(n)
        for p in range(at,at+size):occupied[p]=at
        if owner!='cached':added.append(copy.deepcopy(n));provenance[str(at)]=[owner]
    for n in cached:insert(n,'cached')
    for path,graph in sorted(graphs.items()):
        need(type(graph)is dict and type(graph.get('nodes'))is list and graph['nodes'],'旧graph欠落')
        for n in graph['nodes']:insert(n,path)
    return [known[k]for k in sorted(known)],sorted(added,key=lambda n:n['address']),provenance


def pending_binding(pending,nodes):
    need(pending==sorted((*RESOURCE,*REUSED)),'pending差分')
    addresses={n['address']for n in nodes}
    need(all((p&~1)in addresses for p in REUSED),'旧3entry欠落')
    need(all((p&~1)not in addresses for p in RESOURCE),'resource未読境界差分')
    return {'pending_direct_callees':list(RESOURCE),'known_callees_awaiting_caller_contracts':list(REUSED),
        'all_callees_return_proven':False,'old_byte_samples_repeated':0,'old_abi_contracts_replayed':0}


def archive_checked(raw,spec,report):
    need(identity(raw)['sha256']==spec['digest'],'原ZIP digest差分')
    with zipfile.ZipFile(io.BytesIO(raw))as z:
        infos=z.infolist();names=[i.filename for i in infos]
        need(len(names)==len(set(names))and 0<len(names)<=24,'ZIP member数/重複')
        need(sum(i.file_size for i in infos)<=8_000_000,'ZIP展開上限')
        for i in infos:
            p=Path(i.filename)
            need(len(p.parts)==1 and p.suffix in ('.json','.txt')and not i.is_dir()
                and (i.external_attr>>16)&0o170000!=0o120000,'ZIP非text/path/symlink')
        required={'analysis.json','recorded-result.json','tests.json','guard.json'}
        need(required<=set(names),'ZIP必須原本欠落')
        members={name:z.read(name)for name in names}
    for raw_member in members.values():
        raw_member.decode('utf-8');need(b'\0'not in raw_member,'ZIP text NUL')
    a=strict(members['analysis.json']);receipt=strict(members['recorded-result.json'])
    need(a==report['analysis']and strict(members['tests.json'])==report['focused_tests'],'原analysis/tests不一致')
    need(receipt['status']=='PASS_RECORDED_NONFORCE_PUSHED'and receipt['run_id']==spec['run']
        and receipt['source_head']==spec['source']and receipt['commit']==spec['commit']
        and receipt['tests']==report['focused_tests']and receipt['tests']['tests_run']==spec['tests'],'原receipt差分')
    need(receipt['ring_acquisition_accepted']is False and receipt['release_ready']is False
        and type(receipt['new_emulator_processes'])is int and receipt['new_emulator_processes']==0,'原scope差分')
    guard=strict(members['guard.json'])
    need(guard['new_violations']==0 and guard['exact_output_match']is True and guard['full_guard_pass_claimed']is False
        and guard['full_guard_before']==guard['full_guard_after']==1,'原guard境界差分')
    return {'spec':copy.deepcopy(spec),'archive_identity':identity(raw),'receipt':receipt,'guard':guard,
        'member_identities':{k:identity(v)for k,v in members.items()},'original_conclusion':'success',
        'original_zip_verified':True,'analysis_equal_to_tracked_report':True,'replayed':False}


def discover(root):
    contracts={};samples={}
    for name in NAMES:
        path='content/modernization/pr16_ring_'+name+'.json'
        value=report_checked((root/path).read_bytes(),OLD_HASHES[name]);contracts[path]=value
        for p,binding in byte_paths(value).items():
            raw=(root/p).read_bytes();need(identity(raw)==binding,'保存byte identity差分')
            v=report_checked(raw,binding['sha256']);samples[p]=v
    need(len(samples)==7,'7byte graph期待');return contracts,samples


def analyze(prior,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_dispatch_frontier as frontier
    import pr16_ring_flagset_continuation as saved
    contracts,samples=discover(s.ROOT)
    nodes,_,_=frontier.saved_inputs();r=s.load(frontier.REPORT)
    saved.bindings_fresh(s.ROOT,r['source_bindings']);nodes=[*nodes,*r['analysis']['new_nodes']]
    need(len(nodes)==prior['analysis']['saved_node_count']==2330,'元node数')
    merged,added,provenance=merge_nodes(nodes,{p:v['analysis']['graph']for p,v in samples.items()})
    binding=pending_binding(prior['analysis']['pending_direct_callees'],merged)
    evidence=[]
    for path,value in contracts.items():
        run=s.api('actions/runs/'+str(value['run_id']))
        need(run['status']=='completed'and run['conclusion']=='success'and run['head_sha']==value['source_head'],'旧ABI Actions差分')
        evidence.append({'path':path,'identity':identity((s.ROOT/path).read_bytes()),'run_id':run['id'],
            'source_head':run['head_sha'],'conclusion':run['conclusion'],'native_or_abi_replayed':False})
    stages=[]
    for spec in STAGES:
        path='content/modernization/'+spec['slug']+'.json';report=s.load(path)
        run=s.api('actions/runs/'+str(spec['run']))
        need(run['status']=='completed'and run['conclusion']=='success'and run['head_sha']==spec['source'],'本工程Actions差分')
        job=s.api('actions/jobs/'+str(spec['job']))
        need(job['run_id']==spec['run']and job['conclusion']=='success','本工程job差分')
        subprocess.run(['git','merge-base','--is-ancestor',spec['commit'],'HEAD'],cwd=s.ROOT,check=True)
        need(subprocess.check_output(['git','show',spec['commit']+':'+path],cwd=s.ROOT)==(s.ROOT/path).read_bytes(),'保存commit byte差分')
        raw=subprocess.check_output(['gh','api','repos/'+s.REPO+'/actions/artifacts/'+str(spec['artifact'])+'/zip'],cwd=s.ROOT)
        stages.append(archive_checked(raw,spec,report))
    result={'classification':'SAVED_EXTERNAL_GRAPH_REUSE_AND_SESSION_ORIGINALS_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(CANDIDATE),'cached_node_count':2330,'new_node_count':0,'reused_external_node_count':len(added),
        'saved_node_count':len(merged),'reused_external_nodes':added,'node_source_provenance':provenance,
        'reused_byte_reports':{p:identity((s.ROOT/p).read_bytes())for p in samples},'old_contract_actions_verified':evidence,
        'session_stages_verified_without_replay':stages,**binding,'pending_effective_targets':[],
        'pending_continuations':[],'pending_data_ranges':[],'unbound_runtime_data':copy.deepcopy(prior['analysis']['unbound_runtime_data']),
        'all_callers_resolved':False,'all_live_frames_proven':False,'caller_pointer_size_limit_proven':False,
        'all_runtime_owners_excluded':False,'all_dispatch_returns_proven':False,'all_live_slot_bounds_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':0,'new_byte_samples':0,'saved_nodes_redecoded':0,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0}
    (out/'saved-context.json').write_bytes(s.stable({'nodes':merged,'analysis':result}))
    (out/'analysis.json').write_bytes(s.stable(result))
    return result


def summaries(result):
    return (f'旧external1/2/3の7保存byte graphから{result["reused_external_node_count"]}命令を再利用結合し、合計{result["saved_node_count"]}命令。'
        '今回2工程の61tests・原Actions/job/ZIP/保存commitを再実行なしで照合。実caller契約は未証明のまま。',
        '保存済みselector1/2の3calleeをVarGet callerへ結合し、帰還/SP/record書込と条件不足/容量不足を検証する。'
        '残るresource8callee、実callback table/変数領域allocationは未証明。7旧graphの採取/旧ABI・VarGet全65536値/1337帰還・BP/nativeを単独再実行しない。'
        'Ring正規story取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    import pr16_ring_dispatch_contracts as contracts
    import pr16_ring_dispatch_frontier as frontier
    import pr16_ring_reference_contracts as older
    import pr16_ring_dependency_contracts as old_contracts
    old,byte=discover(support.ROOT)
    SOURCES=tuple(dict.fromkeys((contracts.SELF,frontier.SELF,frontier.REPORT,*old,*byte,
        contracts.prior.SELF,contracts.prior.caller.SELF,contracts.vm.SELF,contracts.vm.flow.SELF,
        *older.SOURCES,*old_contracts.SOURCES)))
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
